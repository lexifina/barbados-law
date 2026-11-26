"""The single network runner for Barbados: one request at a time to www.barbadoslawcourts.gov.bb, 10.5 s apart
(its robots.txt: Crawl-delay 10). Back off on 429/5xx; stop after 3 blocks (403/429/unreachable) in a row.

Order: listing pages; the Constitution and the core statutes; every consolidated statute; the annual Acts;
consolidated subsidiary legislation; annual statutory instruments; then judgments (monthly searches of the public
search form, 2007 on) and their PDFs into caselaw/.

Records each PDF in state/fetched.json (pages, text-layer size, scanned pages, producer, word score).
Re-runnable: skips URLs already recorded. Stop: touch state/fetch.stop.
"""
import os, sys, json, time, hashlib, re, html, urllib.request, urllib.parse, urllib.error, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = "https://www.barbadoslawcourts.gov.bb/"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36"
GAP = 10.5
LOG = os.path.join(ROOT, "progress.log")
IDX = os.path.join(ROOT, "state", "fetched.json")
CAT = os.path.join(ROOT, "catalogue.json")
JIDX = os.path.join(ROOT, "caselaw", "judgments.json")
STOP = os.path.join(ROOT, "state", "fetch.stop")
_last = [0.0]
blocks = [0]


def log(m):
    with open(LOG, "a", encoding="utf8") as f:
        f.write(time.strftime("%Y-%m-%d %H:%M:%S ") + "fetch " + m + "\n")


def load(p, d):
    try:
        return json.load(open(p, encoding="utf8"))
    except Exception:
        return d


def save(p, obj):
    tmp = p + ".tmp"
    json.dump(obj, open(tmp, "w", encoding="utf8"), ensure_ascii=False, indent=0)
    os.replace(tmp, p)


def quote(u):
    p = urllib.parse.urlsplit(u)
    return urllib.parse.urlunsplit((p.scheme, p.netloc, urllib.parse.quote(urllib.parse.unquote(p.path), safe="/'(),&"),
                                    p.query, ""))


def fetch(url, data=None, tries=4):
    backoff = 60
    for t in range(tries):
        d = _last[0] + GAP - time.time()
        if d > 0:
            time.sleep(d)
        _last[0] = time.time()
        try:
            h = {"User-Agent": UA}
            if data:
                h["Content-Type"] = "application/x-www-form-urlencoded"
            with urllib.request.urlopen(urllib.request.Request(quote(url), data=data, headers=h), timeout=180) as r:
                b = r.read()
                blocks[0] = 0
                return r.status, b
        except urllib.error.HTTPError as e:
            if e.code == 429 or e.code >= 500:
                log(f"HTTP {e.code} {url}: backing off {backoff}s")
                if e.code == 429:
                    blocks[0] += 1
                time.sleep(backoff); backoff *= 2
                continue
            if e.code == 403:
                blocks[0] += 1
            return e.code, b""
        except Exception as e:
            log(f"error {type(e).__name__} {url}")
            time.sleep(30)
    blocks[0] += 1
    return -1, b""


def stopped():
    if os.path.exists(STOP):
        log("stop file"); return True
    if blocks[0] >= 3:
        log("STOP: 3 blocks in a row (403/429/unreachable)"); return True
    return False


WORD = re.compile(r"[A-Za-z]+")
COMMON = set("""the of and to in a be or any by for shall such as is on under this act with person may which section that
not from other an at it all made order minister where his provided court time paragraph""".split())


def textinfo(fn):
    try:
        import pymupdf
        d = pymupdf.open(fn)
        chars = scanned = words = good = 0
        for p in d:
            t = p.get_text()
            chars += len(t.strip())
            for img in p.get_image_info():
                x0, y0, x1, y1 = img["bbox"]
                if (x1 - x0) * (y1 - y0) > 0.5 * p.rect.width * p.rect.height:
                    scanned += 1; break
            for w in WORD.findall(t):
                words += 1
                lw = w.lower()
                if lw in COMMON or (len(w) > 2 and (w.islower() or w.istitle() or w.isupper()) and re.search(r"[aeiouy]", lw)):
                    good += 1
        meta = " | ".join(f"{k}={v}" for k, v in (d.metadata or {}).items() if v and k in ("producer", "creator", "creationDate", "modDate"))
        return dict(pages=d.page_count, text_chars=chars, scanned_pages=scanned, word_q=round(good / words, 3) if words else 0, meta=meta[:300])
    except Exception as e:
        return dict(pages=0, text_chars=-1, scanned_pages=0, word_q=0, meta=f"unreadable {type(e).__name__}")


def get_pdf(url, idx, dest, extra=None):
    st, b = fetch(url)
    rec = {"status": st, "bytes": len(b), "at": time.strftime("%Y-%m-%dT%H:%M:%S")}
    rec.update(extra or {})
    if st == 200 and b[:5] == b"%PDF-":
        sha = hashlib.sha256(b).hexdigest()
        fn = os.path.join(dest, sha[:16] + ".pdf")
        if not os.path.exists(fn):
            open(fn, "wb").write(b)
        rec.update(sha256=sha, file=os.path.basename(fn), **textinfo(fn))
    elif st == 200:
        rec["status"] = "not-pdf"
    if st in (403, 429, -1):
        return st, None
    idx[url] = rec
    return st, rec


def page(url, name):
    st, b = fetch(url)
    if st != 200:
        log(f"listing HTTP {st} {url}"); return None
    t = b.decode("utf8", "replace")
    open(os.path.join(ROOT, "html", name + ".html"), "w", encoding="utf8").write(t)
    return t


def links(t, prefix):
    out = []
    for m in re.finditer(r'<a[^>]*href="(' + prefix + r'[^"]+\.pdf)"[^>]*>([\s\S]*?)</a>', t, re.I):
        out.append((BASE + html.unescape(m.group(1)), re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", m.group(2)))).strip()))
    return out


CORE = re.compile(r"(?i)^(ConstitutionofBarbados|Constitution|Interpretation|OffencesAgainstthePerson|Theft|Evidence|"
                  r"SupremeCourtofJudicature|MagistratesCourts|CriminalProcedure|Companies|Citizenship|Representationof"
                  r"thePeople|SexualOffences|Drug|Firearms|Police|Bail|Succession|Property|Landlord|Contracts|SaleofGoods|"
                  r"FamilyLaw|Employment|SeveranceP|IncomeTax|ValueAddedTax|NationalInsurance|Customs|Immigration|"
                  r"PublicOrder|Juries|Coroners|Limitation|Prisons|Penal|Criminal|Domestic|Insolvency|Bankruptcy|Banking)")


def catalogue():
    cat = load(CAT, None)
    if cat:
        return cat
    cat = []
    t = page(BASE + "laws/consolidated-laws/statutes-of-barbados", "statutes")
    for u, ti in links(t or "", "assets/content/pdfs/statutes/"):
        fn = u.rsplit("/", 1)[1]
        cat.append(dict(url=u, title=ti, group="statute", pri=0 if fn.startswith("Constitution") else 1 if CORE.match(fn) else 2))
    t = page(BASE + "laws/annuals/acts-annual", "acts-annual") or ""
    for y in sorted(set(re.findall(r'href="(laws/annuals/acts-annual/acts-(\d{4}))"', t))):
        tt = page(BASE + y[0], "acts-" + y[1]) or ""
        for u, ti in links(tt, "assets/content/pdfs/annuals/"):
            cat.append(dict(url=u, title=ti, group="act", year=int(y[1]), pri=3))
    t = page(BASE + "laws/consolidated-laws/subsidiary-legislation-of-barbados", "subsidiary") or ""
    for u, ti in links(t, "assets/content/pdfs/subsidiary_legislation_of_barbados/"):
        cat.append(dict(url=u, title=ti, group="subsidiary", pri=4))
    t = page(BASE + "laws/annuals/statutory-instruments-%E2%80%93-annual", "sls-annual") or ""
    for y in sorted(set(re.findall(r'href="(laws/annuals/statutory-instruments-[^"]*?/sls-(\d{4}))"', t))):
        tt = page(BASE + "laws/annuals/statutory-instruments-%E2%80%93-annual/sls-" + y[1], "sls-" + y[1]) or ""
        for u, ti in links(tt, "assets/content/pdfs/annuals/"):
            cat.append(dict(url=u, title=ti, group="si", year=int(y[1]), pri=5))
    seen, out = set(), []
    for e in cat:
        if e["url"] not in seen:
            seen.add(e["url"]); out.append(e)
    save(CAT, out)
    log(f"catalogue: {len(out)} PDFs " + json.dumps({g: sum(1 for e in out if e['group'] == g) for g in ('statute', 'act', 'subsidiary', 'si')}))
    return out


ROW = re.compile(r'<p>\d+\.\s*<a href="(judgments/[^"]+)"[^>]*>([\s\S]*?)</a></p>[\s\S]*?<td width="13%">([\s\S]*?)</td>\s*'
                 r'<td>([\s\S]*?)</td>(?:</td>)?\s*<td>([\s\S]*?)</td>\s*<td class="download">([\s\S]*?)</td>')


def search(a, b):
    data = urllib.parse.urlencode([("asId", "as0"), ("search", ""), ("casename", ""), ("judge", ""), ("citation", ""),
                                   ("decision_date", "between"), ("date_between_start_date", a.isoformat()),
                                   ("date_between_end_date", b.isoformat()), ("summary", ""), ("court[]", "all"),
                                   ("submit-search-2", "Search")]).encode()
    st, body = fetch(BASE + "judgments/", data=data)
    if st != 200:
        return None
    t = body.decode("utf8", "replace")
    m = re.search(r"1-(\d+) of (\d+) results shown", t)
    shown, total = (int(m.group(1)), int(m.group(2))) if m else (0, 0)
    rows = []
    for r in ROW.finditer(t):
        cl = lambda s: re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s))).strip()
        pdf = re.search(r'href="([^"]+\.pdf)"', r.group(6), re.I)
        rows.append(dict(page=BASE + r.group(1), title=cl(r.group(2)), court=cl(r.group(3)), judge=cl(r.group(4)),
                         date=cl(r.group(5)), pdf=BASE + html.unescape(pdf.group(1)) if pdf else None))
    return shown, total, rows


def judgments():
    j = load(JIDX, {"months": {}, "cases": {}})
    m0 = datetime.date(2007, 1, 1)
    today = datetime.date.today()
    months = []
    while m0 <= today:
        nxt = (m0.replace(day=28) + datetime.timedelta(days=4)).replace(day=1)
        months.append((m0, nxt - datetime.timedelta(days=1))); m0 = nxt
    for a, b in months:
        key = a.isoformat()[:7]
        if key in j["months"]:
            continue
        if stopped():
            return False
        spans, got = [(a, b)], []
        while spans:
            x, y = spans.pop()
            r = search(x, y)
            if r is None:
                log(f"judgments {x}..{y}: search failed"); return False
            shown, total, rows = r
            if shown < total and x < y:
                mid = x + (y - x) // 2
                spans += [(x, mid), (mid + datetime.timedelta(days=1), y)]
                continue
            got += rows
        for row in got:
            j["cases"][row["page"]] = row
        j["months"][key] = len(got)
        save(JIDX, j)
        log(f"judgments {key}: {len(got)} cases ({len(j['cases'])} listed)")
    idx = load(os.path.join(ROOT, "caselaw", "fetched.json"), {})
    todo = [c for c in j["cases"].values() if c.get("pdf") and c["pdf"] not in idx]
    log(f"judgment PDFs: {len(todo)} to fetch")
    for n, c in enumerate(todo, 1):
        if stopped():
            save(os.path.join(ROOT, "caselaw", "fetched.json"), idx); return False
        st, rec = get_pdf(c["pdf"], idx, os.path.join(ROOT, "caselaw", "pdf"), {"case": c["page"]})
        if n % 20 == 0 or st != 200:
            save(os.path.join(ROOT, "caselaw", "fetched.json"), idx)
        log(f"case {n}/{len(todo)} {st} {(rec or {}).get('pages')}p {(rec or {}).get('text_chars')}ch {c['title'][:60]}")
    save(os.path.join(ROOT, "caselaw", "fetched.json"), idx)
    return True


def ccj():
    """Caribbean Court of Justice appellate judgments on appeal from Barbados (file names NNNN_CCJ_N_AJ_BB), listed
    through the site's public WordPress media API, 1 request a second (robots.txt allows all)."""
    out = os.path.join(ROOT, "caselaw", "ccj.json")
    j = load(out, {"listed": False, "items": {}, "fetched": {}})
    last = [0.0]

    def get(u):
        for t in range(4):
            d = last[0] + 1.0 - time.time()
            if d > 0:
                time.sleep(d)
            last[0] = time.time()
            try:
                with urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": UA}), timeout=180) as r:
                    return r.status, r.read(), dict(r.headers)
            except urllib.error.HTTPError as e:
                if e.code == 429 or e.code >= 500:
                    time.sleep(60 * (t + 1)); continue
                return e.code, b"", {}
            except Exception:
                time.sleep(30)
        return -1, b"", {}
    try:
        if not j.get("listed2"):
            for q, pat in (("BB", r"(?i)(?<![A-Za-z])CCJ[_\- ]?\d+[_\- ]?\(?AJ\)?[_\- ]?(?:BB|Bds)(?![A-Za-z])"),
                           ("BBCV", r"(?i)CCJ[_\- ]?\(?\d+\)?[_\- ]?\(?AJ\)?"), ("BBCR", r"(?i)CCJ[_\- ]?\(?\d+\)?[_\- ]?\(?AJ\)?")):
                pg, pages = 1, 1
                while pg <= pages:
                    st, b, h = get(f"https://ccj.org/wp-json/wp/v2/media?search={q}&mime_type=application/pdf&per_page=100&page={pg}")
                    if st != 200:
                        log(f"ccj list HTTP {st}"); return
                    pages = int(h.get("X-WP-TotalPages") or h.get("x-wp-totalpages") or 1)
                    for m in json.loads(b):
                        u = m.get("source_url") or ""
                        if re.search(pat, u.rsplit("/", 1)[-1]):
                            j["items"][u] = {"date": m.get("date"), "title": html.unescape((m.get("title") or {}).get("rendered", "")), "q": q}
                    pg += 1
            j["listed2"] = True; save(out, j)
            log(f"ccj: {len(j['items'])} Barbados appellate judgment PDFs listed")
        for u in sorted(j["items"]):
            if u in j["fetched"] or os.path.exists(STOP):
                continue
            st, b, _ = get(u)
            rec = {"status": st, "at": time.strftime("%Y-%m-%dT%H:%M:%S")}
            if st == 200 and b[:5] == b"%PDF-":
                sha = hashlib.sha256(b).hexdigest(); fn = os.path.join(ROOT, "caselaw", "pdf", sha[:16] + ".pdf")
                open(fn, "wb").write(b)
                rec.update(sha256=sha, file=os.path.basename(fn), **textinfo(fn))
            j["fetched"][u] = rec; save(out, j)
            log(f"ccj {len(j['fetched'])}/{len(j['items'])} {st} {rec.get('pages')}p {u.rsplit('/', 1)[-1]}")
        log("ccj DONE")
    except Exception as e:
        log(f"ccj error {type(e).__name__}: {e}")


def main():
    import threading
    threading.Thread(target=ccj, daemon=False).start()
    cat = catalogue()
    idx = load(IDX, {})
    todo = [e for e in cat if e["url"] not in idx]
    todo.sort(key=lambda e: (e["pri"], e.get("year", 0), e["url"]))
    log(f"start: {len(todo)} legislation PDFs to fetch, {len(idx)} recorded")
    for n, e in enumerate(todo, 1):
        if stopped():
            save(IDX, idx); sys.exit(2)
        st, rec = get_pdf(e["url"], idx, os.path.join(ROOT, "pdf"), {"title": e["title"], "group": e["group"]})
        if n % 10 == 0 or e["pri"] == 0:
            save(IDX, idx)
        r = rec or {}
        log(f"{n}/{len(todo)} {st} {r.get('pages')}p {r.get('text_chars')}ch scan{r.get('scanned_pages')} q{r.get('word_q')} {e['group']} {e['title'][:60]}")
    save(IDX, idx)
    log("legislation DONE")
    if judgments():
        log("DONE")


if __name__ == "__main__":
    main()
