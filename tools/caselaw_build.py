"""Append Barbados judgments to the private barbados-law-caselaw repository, one file and one commit per judgment.

python -I tools/caselaw_build.py <repo> [--limit N] [--dry]

Sources: the Barbados Law Courts judgments search (caselaw/judgments.json, PDFs in caselaw/fetched.json) and the
Caribbean Court of Justice's appellate judgments on appeal from Barbados (caselaw/ccj.json).
Layout: <court>/<year>/<yyyy-mm-dd>-<slug>.md. Each commit is dated noon America/Barbados on the day of decision: the
date the Law Courts list for the case, or for the CCJ the date of judgment printed in the judgment.
Protected matters (family, children, adoption, sexual offences, mental health, anonymised parties) are left out.
Text: the PDF text layer only; no OCR is run. A judgment with no usable text layer or no date is held."""
import json, os, re, sys, subprocess, datetime, unicodedata, collections

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TODAY = datetime.date(2026, 11, 26)
EMAIL = "barbados-law-caselaw@lexifina.com"
MONTHS = {m: i for i, m in enumerate(["january", "february", "march", "april", "may", "june", "july", "august",
                                      "september", "october", "november", "december"], 1)}
PROTECTED_TITLE = re.compile(
    r"(?i)\b(child|children|minor|juvenile|infant|adoption|custody|guardian(?:ship)?|divorce|matrimonial|family|maintenance|"
    r"sexual|rape|incest|carnal|buggery|indecent|mental health|in camera|anonymi[sz]ed|(?:a|the)\s+minor)\b")
ANON = re.compile(r"(?:^|\bv\.?\s+)(?:[A-Z]\.\s?){1,3}(?=\s+v\b|\s*$|\s+[A-Z][a-z])"
                  r"|\bv\.?\s+[A-Z]{1,3}\s*$|\bv\.?\s+(?:[A-Z]\.?\s?){1,3}$|^[A-Z]{1,3}\s+v\b|^(?:Re|In re)\s+[A-Z]\b")
PROTECTED_HEAD = re.compile(
    r"(?i)(family\s+(?:division|proceedings|court)|matrimonial|divorce|decree\s+nisi|custody\s+of\s+(?:the|a|his|her)\s+"
    r"(?:child|minor|infant)|adoption|Child\s+Care\s+Board|Juvenile|sexual\s+offences?|\brape\b|incest|indecent\s+assault|"
    r"serious\s+indecency|unlawful\s+sexual\s+intercourse|buggery|sexual\s+intercourse\s+with|guardianship|"
    r"Mental\s+Health\s+Act|in\s+camera|anonymi[sz]ed|Domestic\s+Violence)")


def slug(s, n=70):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    s = re.sub(r"[^a-z0-9]+", "-", s.replace("'", "")).strip("-")
    return s[:n].strip("-") or "untitled"


def same_surname(title):
    parts = re.split(r"(?i)\s+v\.?\s+", title)
    if len(parts) != 2:
        return False
    a = re.findall(r"[A-Za-z'-]{3,}", parts[0]); b = re.findall(r"[A-Za-z'-]{3,}", parts[1])
    if not a or not b or re.match(r"(?i)(the|attorney|ag|state|queen|regina|r\b|director|commissioner)", parts[1].strip()):
        return False
    return a[-1].lower() in [x.lower() for x in b[:4]] and a[-1].lower() not in ("ltd", "limited", "inc", "company", "barbados")


def court_of(c):
    s = c.lower()
    if "appeal" in s:
        return "court-of-appeal", "Court of Appeal of Barbados"
    if "magistrate" in s:
        return "magistrates-courts", "Magistrates' Courts of Barbados"
    if "registrar" in s:
        return "registrars-court", "Registrar's Court, Supreme Court of Barbados"
    return "high-court", "High Court of Barbados" + (f" ({c.split(',', 1)[1].strip()})" if "," in c else "")


def pdf_text(fn):
    import pymupdf
    d = pymupdf.open(fn)
    t = "\n".join(p.get_text() for p in d).replace("\r", "")
    t = re.sub(r"[ \t]+\n", "\n", t)
    t = re.sub(r"\n{3,}", "\n\n", t)
    return t.strip() + "\n", d.page_count


def git_when(d, seq):
    t = int(datetime.datetime(d.year, d.month, d.day, 16, 0, tzinfo=datetime.timezone.utc).timestamp())
    return f"{t} -0400"


def ccj_date(t, cite_year=None):
    pats = [r"(?i)Date\s+of\s+(?:Judgment|Reasons|Decision)\s*:?\s*(\d{1,2})(?:st|nd|rd|th)?\s+(?:day\s+of\s+)?([A-Za-z]+),?\s+(\d{4})",
            r"(?i)Delivered\s+(?:jointly\s+)?by.{0,400}?\bon\s+the\s+(\d{1,2})(?:st|nd|rd|th)?\s+(?:day\s+of\s+)?([A-Za-z]+),?\s+(\d{4})"]
    for pat in pats:
        m = re.search(pat, t[:15000], re.S)
        if m and m.group(2).lower() in MONTHS:
            try:
                d = datetime.date(int(m.group(3)), MONTHS[m.group(2).lower()], int(m.group(1)))
            except ValueError:
                continue
            if cite_year is None or abs(d.year - cite_year) <= 1:
                return d
    return None


def ccj_title(s):
    m = re.search(r"((?:19|20)\d\d)[^0-9]+CCJ[^0-9]*?(\d+)", s)
    return f"[{m.group(1)}] CCJ {int(m.group(2))} (AJ)" if m else s


def done_sources(repo):
    r = subprocess.run(["git", "-C", repo, "log", "--format=%(trailers:key=Source,valueonly,separator=%x0A)", "main"],
                       capture_output=True, text=True, encoding="utf-8")
    return {x.strip() for x in r.stdout.split("\n") if x.strip()}


def main():
    repo = sys.argv[1]
    limit = int(sys.argv[sys.argv.index("--limit") + 1]) if "--limit" in sys.argv else None
    have = done_sources(repo)
    held, rows, used = [], [], set()
    load = lambda p, d: json.load(open(p, encoding="utf-8")) if os.path.exists(p) else d
    lc = load(os.path.join(ROOT, "caselaw", "judgments.json"), {"cases": {}})
    lf = load(os.path.join(ROOT, "caselaw", "fetched.json"), {})
    cj = load(os.path.join(ROOT, "caselaw", "ccj.json"), {"items": {}, "fetched": {}})
    items = []
    for c in lc["cases"].values():
        r = lf.get(c.get("pdf") or "")
        if not r:
            continue
        m = re.match(r"(\d{2})/(\d{2})/(\d{4})$", c.get("date", ""))
        d = datetime.date(int(m.group(3)), int(m.group(2)), int(m.group(1))) if m else None
        folder, cname = court_of(c.get("court", ""))
        items.append(dict(url=c["pdf"], page=c["page"], title=c["title"], judge=c.get("judge", ""), court=folder,
                          cname=cname, date=d, basis="date of decision listed by the Barbados Law Courts", rec=r))
    for u, r in cj.get("fetched", {}).items():
        it = cj["items"].get(u, {})
        items.append(dict(url=u, page=None, title=ccj_title(it.get("title") or u.rsplit("/", 1)[-1]), judge="", court="caribbean-court-of-justice",
                          cname="Caribbean Court of Justice (appellate jurisdiction)", date=None,
                          basis="date of judgment printed in the judgment", rec=r))
    seen = set()
    for it in items:
        u, r, title = it["url"], it["rec"], re.sub(r"\s+", " ", it["title"]).strip()
        if u in have:
            continue
        if r.get("status") != 200 or not r.get("file"):
            held.append((u, title, f"not fetched (HTTP {r.get('status')})")); continue
        fn = u.rsplit("/", 1)[-1]
        if it["court"] == "caribbean-court-of-justice":
            if re.search(r"(?i)[_-]S(?:UMMARY)?\.pdf$", fn):
                held.append((u, title, "judgment summary, not the judgment")); continue
            key = re.sub(r"(?i)(?:[-_ ]\d)?\.pdf$", "", fn).replace("-", "_").lower()
            if key in seen:
                held.append((u, title, "another upload of the same judgment")); continue
            seen.add(key)
        if r["sha256"] in seen:
            continue
        seen.add(r["sha256"])
        if PROTECTED_TITLE.search(title) or ANON.search(title) or same_surname(title) or re.match(r"(?i)FL\d", fn):
            held.append((None, "(protected)", "protected matter (family, children, sexual offence or anonymised party)")); continue
        if (r.get("text_chars") or 0) < 200 * max(1, r.get("pages") or 1) or (r.get("word_q") or 0) < 0.8:
            held.append((u, title, "no usable text layer (page scans); no OCR is run here")); continue
        text, pages = pdf_text(os.path.join(ROOT, "caselaw", "pdf", r["file"]))
        if it["court"] == "caribbean-court-of-justice" and not re.search(
                r"(?is)on\s+appeal\s+from.{0,300}barbados|BB(?:CV|CR)\s*\d{4}", text[:6000]):
            held.append((u, title, "not an appeal from Barbados")); continue
        if PROTECTED_HEAD.search(text[:6000]):
            held.append((None, "(protected)", "protected matter (family, children, sexual offence or anonymised party)")); continue
        cy = re.match(r"\[?((?:19|20)\d\d)", fn)
        d = it["date"] or (ccj_date(text, int(cy.group(1)) if cy else None) if it["court"] == "caribbean-court-of-justice" else None)
        if not d or d > TODAY:
            held.append((u, title, "no date of decision found")); continue
        path = f"{it['court']}/{d.year}/{d.isoformat()}-{slug(title)}.md"
        j = 2
        while path in used:
            path = f"{it['court']}/{d.year}/{d.isoformat()}-{slug(title)}-{j}.md"; j += 1
        used.add(path)
        head = f"# {title}\n\n{it['cname']}" + (f" · {it['judge']}" if it["judge"] else "") + f" · {d.isoformat()}\n\n"
        rows.append(dict(date=d, path=path, body=head + text, author=it["cname"], title=title, judge=it["judge"],
                         trailers=[("Decided", d.isoformat()), ("Decided-basis", it["basis"]), ("Court", it["cname"])]
                         + ([("Judge", it["judge"])] if it["judge"] else []) + ([("Case-page", it["page"])] if it["page"] else [])
                         + [("Text-source", "PDF text layer"), ("Source", u), ("Source-sha256", r["sha256"])], pages=pages))
    rows.sort(key=lambda x: (x["date"], x["path"]))
    if limit:
        rows = rows[:limit]
    json.dump([{"url": u, "title": t, "why": w} for u, t, w in held], open(os.path.join(ROOT, "caselaw", "held.json"), "w",
              encoding="utf-8"), ensure_ascii=False, indent=1)
    if "--dry" in sys.argv:
        print(len(rows), "rows;", len(held), "held", collections.Counter(h[2][:30] for h in held))
        for r in rows[:: max(1, len(rows) // 20)]:
            print(r["date"], r["path"])
        return
    if not rows:
        print("nothing new"); return
    parent = subprocess.run(["git", "-C", repo, "rev-parse", "--verify", "-q", "main"], capture_output=True, text=True).stdout.strip()
    p = subprocess.Popen(["git", "-C", repo, "fast-import", "--quiet", "--done"], stdin=subprocess.PIPE, creationflags=0x08000000)
    w = p.stdin

    def data(b):
        w.write(f"data {len(b)}\n".encode()); w.write(b); w.write(b"\n")
    for seq, r in enumerate(rows):
        msg = (f"{r['title']} ({r['author']}, {r['date'].isoformat()})\n\nJudgment as published, {r['pages']} pages; "
               "the text is the PDF's text layer.\n\n" + "".join(f"{k}: {v}\n" for k, v in r["trailers"]))
        when = git_when(r["date"], seq)
        w.write(b"commit refs/heads/main\n")
        w.write(f"author {r['author']} <judgments@barbadoslawcourts.gov.bb.invalid> {when}\ncommitter Lexifina <{EMAIL}> {when}\n".encode("utf-8"))
        data(msg.encode("utf-8"))
        if seq == 0 and parent:
            w.write(f"from {parent}\n".encode())
        w.write(f"M 100644 inline {r['path']}\n".encode("utf-8")); data(r["body"].encode("utf-8"))
        w.write(b"\n")
    w.write(b"done\n"); w.close(); p.wait()
    print(f"committed {len(rows)}; held {len(held)}; fast-import rc {p.returncode}")


if __name__ == "__main__":
    main()
