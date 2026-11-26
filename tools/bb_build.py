"""Append the law of Barbados to the barbados-law repository as git fast-import commits on main.

python -I tools/bb_build.py <repo> [--limit N] [--dry]

Source: Barbados Law Courts PDFs (state/fetched.json + pdf/), the text layer only. No OCR is run here; a text layer
the publisher made over page scans is taken only when it reads cleanly, and tagged "publisher OCR".
Layout (STRUCTURE.md): constitution/; revised-laws/cap-NNN-<slug>/ (+ subsidiary/<slug>/); acts/<year>/<NNN>-<slug>/;
subsidiary/<year>/<NNN>-<slug>/ -- one file per section. One commit per version, dated noon America/Barbados
(UTC-04:00, no daylight saving) on its in-force day. Instruments already committed (Source/Consolidated trailer) are
skipped. Nothing is dated by the day it was retrieved: with no date in the text the instrument is held.
"""
import json, os, re, subprocess, sys, datetime, unicodedata, collections

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TODAY = datetime.date(2026, 11, 26)
MONTHS = {m: i for i, m in enumerate(["january", "february", "march", "april", "may", "june", "july", "august",
                                      "september", "october", "november", "december"], 1)}
MONTHS.update({m[:3]: i for m, i in list(MONTHS.items())}); MONTHS["sept"] = 9
HELD = []
EMAIL = "barbados-law@lexifina.com"
INVALID = "barbadoslawcourts.gov.bb.invalid"


def slug(s, n=60):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    s = re.sub(r"^the\s+", "", s.strip())
    s = re.sub(r"[^a-z0-9]+", "-", s.replace("'", "")).strip("-")
    return s[:n].strip("-") or "untitled"


def numkey(n):
    m = re.match(r"(\d+)([A-Z]*)", n)
    return (int(m.group(1)), m.group(2))


SEC = re.compile(r"^((?:\d{1,3})[A-Z]{0,2})\s?\.\s*(?:[-â€”â€“]+\s*)?(?=[(A-Z\"'â€œâ€˜\d*])", re.M)
SCHED = re.compile(r"^\s*(?:(?:FIRST|SECOND|THIRD|FOURTH|FIFTH|SIXTH|SEVENTH|EIGHTH|NINTH|TENTH|ELEVENTH|TWELFTH)\s+)?"
                   r"SCHEDULE(?:\s+[0-9IVX]+)?\s*\.?\s*$", re.M)


def split_sections(text):
    ms = list(SEC.finditer(text))
    starts = [i for i, m in enumerate(ms) if m.group(1) == "1"]
    if not starts:
        return None
    cands = []
    for s in starts:
        seq, last = [ms[s]], numkey("1")
        for m in ms[s + 1:]:
            k = numkey(m.group(1))
            if k > last and k[0] <= last[0] + 3:
                seq.append(m); last = k
        cands.append(seq)
    top = max(len(c) for c in cands)

    def body(c):
        ends = [m.start() for m in c[1:]] + [len(text)]
        return sum(1 for m, e in zip(c, ends) if e - m.start() >= 120)
    seq = max((c for c in cands if len(c) >= 0.6 * top), key=lambda c: (body(c), c[-1].start() - c[0].start(), len(c)))
    if len(seq) < 2:
        return None
    files = []
    head = text[:seq[0].start()].strip()
    if head:
        files.append(("preamble.md", head))
    sm = [m for m in SCHED.finditer(text) if m.start() > seq[-1].start()]
    end_body = sm[0].start() if sm else len(text)
    seen = set()
    for i, m in enumerate(seq):
        e = seq[i + 1].start() if i + 1 < len(seq) else end_body
        n = m.group(1)
        name = f"sec-{int(re.match(r'[0-9]+', n).group()):03d}{re.sub(r'^[0-9]+', '', n).lower()}.md"
        if name in seen:
            return None
        seen.add(name)
        files.append((name, text[m.start():e].strip()))
    for j, s in enumerate(sm):
        e = sm[j + 1].start() if j + 1 < len(sm) else len(text)
        files.append((f"schedule-{j + 1:02d}.md", text[s.start():e].strip()))
    return files


DAY = r"(\d{1,2})\s*(?:st|nd|rd|th)?\s*(?:day\s+)?(?:of\s+)?([A-Za-z]{3,9})\.?,?\s+(\d{4})"


def mkdate(dd, mm, yy):
    mm = mm.lower()
    if mm not in MONTHS:
        return None
    try:
        return datetime.date(int(yy), MONTHS[mm], int(dd))
    except ValueError:
        return None


def find(pat, t, lim=8000):
    for m in re.finditer(pat, t[:lim], re.I | re.S):
        d = mkdate(*m.groups()[-3:])
        if d:
            return d
    return None


def dating(text, year, is_act):
    ok = lambda d: d and (year is None or -1 <= d.year - year <= 3) and d <= TODAY
    c = find(r"(?:come|comes|came)\s+into\s+(?:operation|force|effect)\s+on\s+(?:the\s+)?" + DAY, text, 30000)
    if ok(c):
        return c, "commencement day stated in the text"
    b = find(r"\[\s*(?:Commencement:?\s*)?" + DAY + r"\s*\]", text, 8000)
    if ok(b):
        return b, "date of commencement printed under the long title"
    g = find(r"(?:Gazetted|Published in the Official Gazette|Official Gazette)\D{0,40}?" + DAY, text, 8000)
    if ok(g):
        why = "day of publication in the Official Gazette printed in the text"
        if re.search(r"(?:come|comes)\s+into\s+(?:operation|force)\s+on\s+(?:such|a)\s+(?:date|day)", text[:30000], re.I):
            why += " (the text commences on a day to be appointed; that day is not recorded here)"
        return g, why
    if is_act:
        a = find(r"(?:I\s+assent|Assent(?:ed)?)\W.{0,250}?" + DAY, text, 6000)
        if ok(a):
            return a, "day of the Governor-General's assent printed at the head of the Act (no commencement or Gazette day found)"
        p = find(r"(?:Read\s+three\s+times\s+and\s+)?passed\s+the\s+(?:House\s+of\s+Assembly|Senate).{0,80}?" + DAY, text, 400000)
        if ok(p):
            return p, "day the Act passed Parliament, printed at its end (no commencement, Gazette or assent day found)"
    mde = find(r"(?:Made\s+by.{0,250}?(?:this\s+)?|Dated\s+(?:this\s+)?)" + DAY, text, 400000)
    if ok(mde):
        return mde, "day the instrument was made, as printed in it (no commencement or Gazette day found)"
    return None, None


HEAD = re.compile(r"^(?:THE LAWS OF BARBADOS|L\.\s?R\.\s?O\.\s*\d{4}.*|\d{1,4}[A-Z]{0,2}|[-â€“â€”. ]*\d{1,4}[-â€“â€”. ]*|"
                  r"(?:\d+\s+)?CAP\.?\s*\d+[A-Z]*\.?(?:\s+\d+)?|ss?\.\s*\d+[A-Z]*(?:\s*-\s*\d+[A-Z]*)?|"
                  r"Printed by the Government Printer.*|by the authority of the Government.*)$", re.I)
ACTREF = re.compile(r"\b((?:18|19|20)\d\d)-(\d{1,3})\b")
LRO = re.compile(r"L\.\s?R\.\s?O\.\s*((?:19|20)\d\d)")
OCR_META = re.compile(r"(?i)paper capture|abbyy|finereader|omnipage|readiris|\bocr\b|scan|capture|clearscan|tesseract")


def read_pdf(fn, ocr):
    """(body text, margin text, page count). Born-digital: lines set well below the body size are marginal notes
    (section headings and the Acts that made or amended a section) and go to the margin text. Publisher-OCR layers
    have no reliable sizes: everything is body."""
    import pymupdf
    d = pymupdf.open(fn)
    pages, sizes = [], collections.Counter()
    for p in d:
        lines = []
        for b in p.get_text("dict")["blocks"]:
            for l in b.get("lines", []):
                t = "".join(s["text"] for s in l["spans"]).rstrip()
                if not t.strip():
                    continue
                sz = max(s["size"] for s in l["spans"])
                sizes[round(sz)] += len(t)
                lines.append((round(l["bbox"][1], 1), l["bbox"][0], sz, t))
        lines.sort(key=lambda x: (x[0], x[1]))
        pages.append(lines)
    body_size = sizes.most_common(1)[0][0] if sizes else 12
    freq = collections.Counter()
    for pg in pages:
        for ln in set(x[3].strip() for x in pg[:4] + pg[-3:]):
            freq[ln] += 1
    n = len(pages)
    rh = {ln for ln, c in freq.items() if n >= 3 and c >= 3 and c >= 0.25 * n and len(ln) < 90}
    body, margin = [], []
    for pg in pages:
        # merge fragments sharing a baseline (pymupdf splits a line at tab stops)
        merged = []
        for y, x, sz, t in pg:
            if merged and abs(merged[-1][0] - y) < 2.0 and (sz >= 0.85 * body_size) == (merged[-1][2] >= 0.85 * body_size):
                merged[-1] = (merged[-1][0], merged[-1][1], max(merged[-1][2], sz), merged[-1][3] + " " + t.strip())
            else:
                merged.append((y, x, sz, t))
        for i, (y, x, sz, t) in enumerate(merged):
            s = t.strip()
            edge = i < 5 or i >= len(merged) - 3
            if edge and (HEAD.fullmatch(s) or s in rh or (len(s) < 110 and LRO.search(s))):
                continue
            if not ocr and sz < 0.85 * body_size:
                margin.append(s)
            else:
                body.append(s)
    t = "\n".join(body)
    t = re.sub(r"[ \t]+", " ", t)
    t = re.sub(r"\n{3,}", "\n\n", t)
    return t.strip() + "\n", "\n".join(margin), d.page_count


def git_when(d, seq):
    t = int(datetime.datetime(d.year, d.month, d.day, 16, 0, tzinfo=datetime.timezone.utc).timestamp())
    if t < 0:
        t = 16 * 3600 + seq
    return f"{t} -0400"


def done_sources(repo):
    r = subprocess.run(["git", "-C", repo, "log", "--format=%(trailers:key=Source,valueonly,separator=%x0A)%n"
                        "%(trailers:key=Consolidated,valueonly,separator=%x0A)", "main"],
                       capture_output=True, text=True, encoding="utf-8")
    return {x.strip() for x in r.stdout.split("\n") if x.strip()}


def capof(s):
    m = re.search(r"(?i)\bCAP\.?\s*(\d{1,3})([A-Z]?)(?:'([A-Z]))?", s)
    return (f"{int(m.group(1)):03d}{m.group(2).lower()}", m.group(3)) if m else (None, None)


def short_title_from(text, fallback):
    m = re.search(r"may\s+be\s+cited\s+as\s+the\s+([^.;]{3,160}?\b(?:Act|Regulations|Order|Rules|Notice|Proclamation|"
                  r"By-?laws|Resolution)(?:,?\s*(?:18|19|20)\d\d)?)\b", text[:20000].replace("\n", " "))
    return re.sub(r"\s+", " ", m.group(1)).strip() if m else fallback


def catname(title):
    t = re.sub(r"(?i)\s*CAP\.?\s*\d+[A-Z]*('?[A-Z])?\s*$", "", title).strip()
    return re.sub(r"\s+", " ", t)


def consolidated_date(text, margin, ocr):
    """The consolidated editions print the year of their L.R.O. edition and, in the margin, the Acts that made and
    amended each part, but no 'law as at' day."""
    refs = ACTREF.findall(margin if not ocr else text)
    refs = sorted({(int(y), int(n)) for y, n in refs if 1600 < int(y) <= TODAY.year})
    lro = [int(y) for y in LRO.findall(text + "\n" + margin) if int(y) <= TODAY.year]
    # the raw page text (running heads) carries the L.R.O. year; read_pdf removed it from the body, so look at both
    lro_y = max(lro) if lro else None
    if len(refs) <= 1:
        b = find(r"\[\s*(?:Commencement:?\s*)?" + DAY + r"\s*\]", text, 8000)
        if b and b <= TODAY and (not refs or abs(b.year - refs[0][0]) <= 3):
            who = f"Act {refs[0][0]}-{refs[0][1]}" if refs else None
            return b, "date of commencement printed under the long title (the edition names no amending Act)", who
    late = max([y for y, _ in refs] + ([lro_y] if lro_y else []), default=None)
    if not late:
        return None, None, None
    basis = (f"placeholder: 31 December {late}; the edition states no day of its own; "
             + (f"it is the L.R.O. {lro_y} edition" if lro_y else "no L.R.O. year was read")
             + (f" and cites Acts up to {max(y for y, _ in refs)}" if refs else ""))
    return datetime.date(late, 12, 31), basis, None


def plan(have, used):
    rows = []
    idx = json.load(open(os.path.join(ROOT, "state", "fetched.json"), encoding="utf-8"))
    cat = json.load(open(os.path.join(ROOT, "catalogue.json"), encoding="utf-8"))
    capname = {}
    for e in cat:
        if e["group"] == "statute":
            c, _ = capof(e["title"] + " " + e["url"].rsplit("/", 1)[-1])
            if c and c not in capname:
                capname[c] = slug(catname(e["title"]))
    existing = {}
    for u in used:
        m = re.match(r"revised-laws/cap-(\d{3}[a-z]?)-", u)
        if m and u.count("/") == 1:
            existing[m.group(1)] = u
    seen_sha = set()
    order = {"constitution": 0, "statute": 1, "act": 2, "subsidiary": 3, "si": 4}
    items = sorted(idx.items(), key=lambda kv: (0 if "Constitution" in kv[0] else order.get(kv[1].get("group"), 5), kv[0]))
    for url, r in items:
        title = re.sub(r"\s+", " ", r.get("title") or "").strip()
        if url in have:
            continue
        if r.get("status") != 200 or not r.get("file"):
            HELD.append((url, title, f"not fetched (HTTP {r.get('status')})")); continue
        if r["sha256"] in seen_sha:
            HELD.append((url, title, "same file as another entry")); continue
        seen_sha.add(r["sha256"])
        pages = max(1, r.get("pages") or 1)
        ocr = bool(r.get("scanned_pages")) or bool(OCR_META.search(r.get("meta") or ""))
        if (r.get("text_chars") or 0) < 150 * pages:
            HELD.append((url, title, f"no usable text layer ({r.get('pages')} pages, {r.get('text_chars')} characters): page scans; no OCR is run here")); continue
        if (r.get("word_q") or 0) < (0.9 if ocr else 0.8):
            HELD.append((url, title, f"publisher text layer unreadable (word score {r.get('word_q')})")); continue
        row = make_row(url, r, title, ocr, capname, existing, used)
        if row:
            rows.append(row)
    return rows


def make_row(url, r, title, ocr, capname, existing, used):
    text, margin, npages = read_pdf(os.path.join(ROOT, "pdf", r["file"]), ocr)
    raw_lro = ""
    try:
        import pymupdf
        d = pymupdf.open(os.path.join(ROOT, "pdf", r["file"]))
        raw_lro = " ".join(LRO.findall(" ".join(pg.get_text() for pg in d)))
        raw_lro = " ".join(f"L.R.O. {y}" for y in raw_lro.split())
    except Exception:
        pass
    tsrc = ("publisher OCR (the text layer the publisher made over page scans, as served; no OCR was run here)" if ocr
            else "PDF text layer")
    group = r.get("group")
    fn = url.rsplit("/", 1)[-1]
    kind = "publisher"
    if group == "statute":
        if fn.startswith("Constitution") or fn.startswith("BarbadosIndependence"):
            if fn != "ConstitutionofBarbados.pdf":
                d, basis = dating(text, int(re.search(r"(\d{4})", fn).group(1)) if re.search(r"\d{4}", fn) else None, True)
                if not d:
                    HELD.append((url, title, "no date found in the text")); return None
                yr = int(re.search(r"(\d{4})", fn).group(1))
                folder = f"acts/{yr}/" + slug(catname(title))
                author, email, kind = catname(title), f"{slug(catname(title), 40)}@{INVALID}", "enactment"
                subject = f"{catname(title)}: as published, in force {d.isoformat()}"
                lines = [f"{catname(title)}, as published by the Barbados Law Courts."]
            else:
                d, basis, who = consolidated_date(text, margin + "\n" + raw_lro, ocr)
                if not d:
                    HELD.append((url, title, "no date or edition year found")); return None
                folder = "constitution"
                author, email = "Law Revision Office", f"law-revision-office@{INVALID}"
                subject = "The Constitution of Barbados (L.R.O. consolidated text)"
                lines = ["The Constitution of Barbados (Schedule to the Barbados Independence Order 1966), as consolidated",
                         "by the Law Revision Office and published by the Barbados Law Courts. Amendments after that",
                         "edition (among them the Constitution (Amendment) (No. 2) Act 2021, which made Barbados a",
                         "republic on 30 November 2021) are not applied here."]
        else:
            cap, _ = capof(fn + " " + title)
            if not cap:
                HELD.append((url, title, "no chapter number in the file name")); return None
            d, basis, who = consolidated_date(text, margin + "\n" + raw_lro, ocr)
            if not d:
                HELD.append((url, title, "no date or edition year found")); return None
            name = short_title_from(text, catname(title) + " Act")
            folder = existing.get(cap) or f"revised-laws/cap-{cap}-{capname.get(cap) or slug(catname(title))}"
            if who:
                author, email, kind = who, f"act-{who.split()[1]}@{INVALID}", "law"
            else:
                author, email = "Law Revision Office", f"law-revision-office@{INVALID}"
            capd = f"{int(cap[:3])}{cap[3:].upper()}"
            subject = f"{name}, Cap. {capd}: L.R.O. consolidated text"
            lines = [f"{name}, Chapter {capd} of the Laws of Barbados, as consolidated by the Law Revision Office and",
                     "published by the Barbados Law Courts."]
    elif group == "subsidiary":
        cap, letter = capof(fn + " " + title)
        if not cap:
            HELD.append((url, title, "no chapter number in the file name")); return None
        name = re.sub(r"\s*Cap\s*\d+[A-Z]*'?[A-Z]?\s*$", "", title, flags=re.I).strip()
        d, basis, who = consolidated_date(text, margin + "\n" + raw_lro, ocr)
        if not d or (not who and not LRO.search(raw_lro + margin)):
            yr = re.search(r"\b((?:18|19|20)\d\d)\b", name)
            d2, b2 = dating(text, int(yr.group(1)) if yr else None, False)
            if d2:
                d, basis = d2, b2
        if not d:
            HELD.append((url, title, "no date found in the text")); return None
        parent = existing.get(cap) or f"revised-laws/cap-{cap}-{capname.get(cap) or 'chapter'}"
        folder = f"{parent}/subsidiary/{slug(name)}"
        author, email = "Law Revision Office", f"law-revision-office@{INVALID}"
        capd = f"{int(cap[:3])}{cap[3:].upper()}"
        subject = f"{name} (under Cap. {capd}): consolidated subsidiary legislation"
        lines = [f"{name}: subsidiary legislation under Chapter {capd} of the Laws of Barbados, as consolidated and published",
                 "by the Barbados Law Courts."]
    elif group in ("act", "si"):
        m = re.search(r"(?i)(?:Act|SI)\s*((?:19|20)\d\d)[-_ ]*(?:No\.?\s*)?(\d{1,3})", fn)
        if not m:
            HELD.append((url, title, "no number in the file name")); return None
        yr, num = int(m.group(1)), int(m.group(2))
        d, basis = dating(text, yr, group == "act")
        if not d:
            HELD.append((url, title, "no date found in the text")); return None
        if d > TODAY:
            HELD.append((url, title, f"in force {d} after the build day")); return None
        what = "Act" if group == "act" else "Statutory Instrument"
        name = short_title_from(text, f"{what} {yr}-{num}")
        top = "acts" if group == "act" else "subsidiary"
        folder = f"{top}/{yr}/{num:03d}-{slug(re.sub(r',?\s*(?:18|19|20)\d\d$', '', name))}"
        if group == "act":
            author, email = f"Act {yr}-{num}", f"act-{yr}-{num}@{INVALID}"
        else:
            author, email = f"S.I. {yr} No. {num}", f"si-{yr}-{num}@{INVALID}"
        kind = "enactment"
        subject = f"{name}: as {'enacted' if group == 'act' else 'made'}, in force {d.isoformat()}"
        lines = [f"{name} ({author}), as published in the annual volume by the Barbados Law Courts."]
    else:
        return None
    if d > TODAY:
        HELD.append((url, title, f"in force {d} after the build day")); return None
    files = split_sections(text) or [("text.md", text)]
    lines.append(f"{npages} pages. " + ("Marginal notes (section headings and the Acts that made or amended each section) "
                                        "are left out of the text." if not ocr else
                                        "A text layer the publisher made from page scans, with its recognition errors; "
                                        "marginal notes are mixed in where the layer places them."))
    lines.append("One file: no section numbering was found to split on." if len(files) == 1 else
                 f"{len(files)} files: the front matter, one per section and each schedule.")
    if folder in used and not (group == "statute" and folder.startswith("revised-laws/") and folder.count("/") == 1) \
            and folder != "constitution":
        base, j = folder, 2
        while folder in used:
            folder = f"{base}-{j}"; j += 1
    used.add(folder)
    order = 0 if folder == "constitution" else 1 if group == "statute" else 2 if group == "act" else 3
    replace = False
    return dict(order=order, date=d, folder=folder, files=files, author=author, email=email, kind=kind, subject=subject,
                lines=lines, replace=replace,
                trailers=[("In-force", d.isoformat()), ("In-force-basis", basis), ("Text-source", tsrc),
                          ("Source", url), ("Source-sha256", r["sha256"])])


def main():
    repo = sys.argv[1]
    limit = int(sys.argv[sys.argv.index("--limit") + 1]) if "--limit" in sys.argv else None
    have = done_sources(repo)
    ls = subprocess.run(["git", "-C", repo, "ls-tree", "-d", "--name-only", "-r", "main"], capture_output=True, text=True).stdout
    used = set(ls.split())
    rows = plan(have, used)
    rows.sort(key=lambda r: (r["order"], r["date"], r["folder"]))
    if limit:
        rows = rows[:limit]
    json.dump([{"url": u, "title": t, "why": w} for u, t, w in HELD], open(os.path.join(ROOT, "held.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    if "--dry" in sys.argv:
        print(len(rows), "rows;", len(HELD), "held", collections.Counter(h[2][:30] for h in HELD))
        for r in rows[:: max(1, len(rows) // 30)]:
            print(r["date"], r["folder"], len(r["files"]), r["author"], "|", r["trailers"][1][1][:70])
        return
    if not rows:
        print("nothing new"); return
    parent = subprocess.run(["git", "-C", repo, "rev-parse", "main"], capture_output=True, text=True).stdout.strip()
    p = subprocess.Popen(["git", "-C", repo, "fast-import", "--quiet", "--done"], stdin=subprocess.PIPE,
                         creationflags=0x08000000)
    w = p.stdin

    def data(b):
        w.write(f"data {len(b)}\n".encode()); w.write(b); w.write(b"\n")
    for seq, r in enumerate(rows):
        msg = r["subject"] + "\n\n" + "\n".join(r["lines"]) + "\n\n" + f"Kind: {r['kind']}\n" + \
            "".join(f"{k}: {v}\n" for k, v in r["trailers"])
        when = git_when(r["date"], seq)
        w.write(b"commit refs/heads/main\n")
        w.write(f"author {r['author']} <{r['email']}> {when}\ncommitter Lexifina <{EMAIL}> {when}\n".encode("utf-8"))
        data(msg.encode("utf-8"))
        if seq == 0:
            w.write(f"from {parent}\n".encode())
        if r["replace"]:
            w.write(f"D {r['folder']}\n".encode("utf-8"))
        for name, txt in r["files"]:
            w.write(f"M 100644 inline {r['folder']}/{name}\n".encode("utf-8")); data((txt.strip() + "\n").encode("utf-8"))
        w.write(b"\n")
    w.write(b"done\n"); w.close(); p.wait()
    print(f"committed {len(rows)}; held {len(HELD)}; fast-import rc {p.returncode}")


if __name__ == "__main__":
    main()

