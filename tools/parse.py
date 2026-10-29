"""Barbados: three Acts from the born-digital PDFs on barbadoslawcourts.gov.bb (Laws of Barbados, consolidated). Reads .cache only."""
import collections, hashlib, json, re
from pathlib import Path
import pymupdf
here = Path(__file__).parent
BASE = 'https://www.barbadoslawcourts.gov.bb/assets/content/pdfs/statutes/'
ACTS = [
 ('computer-misuse', 'Computer Misuse', 'Computer Misuse Act, Cap. 124B', 'ComputerMisuseCAP124B', '2007'),
 ('anti-terrorism', 'Anti-Terrorism', 'Anti-Terrorism Act, Cap. 158', 'Anti-TerrorismCAP158', '2002'),
 ('bail', 'Bail', 'Bail Act, Cap. 122A', 'BailCAP122A', ''),
]
JUNK = re.compile(r'(\d+\s+)?L\.R\.O\. ?\d{4}(\s+\d+)?|ss?\.[\w,.\s–-]+|CAP\. ?\d+[A-Z]?|THE LAWS OF BARBADOS|\.|[A-Z][A-Za-z\- ]+ +L\.R\.O\. \d{4} \d+|CAP\. \d+[A-Z]? .*L\.R\.O\..*|\d+ L\.R\.O\..*|.*L\.R\.O\. ?\d{4}.*')

def lines(pdf, lo=11.4):
    out = []
    for p in pymupdf.open(pdf):
        rows = collections.defaultdict(list)
        for b in p.get_text('dict')['blocks']:
            for l in b.get('lines', []):
                for s in l['spans']:
                    if lo <= s['size'] <= 12.6 and s['bbox'][1] > 100:
                        rows[round(s['bbox'][1] / 4)].append((s['bbox'][0], s['text'], 'Italic' in s['font']))
        for k in sorted(rows):
            if all(it for _, _, it in rows[k]) and not re.fullmatch(r'\(\w+\)', ''.join(x for _, x, _ in rows[k]).strip()):
                continue
            t = re.sub(r'\s+', ' ', ''.join(x for _, x, _ in sorted(rows[k])).replace('\xa0', ' ')).strip()
            if t and not JUNK.fullmatch(t):
                out.append(t)
    return out

def parse(slug, short, title, f, _):
    pdf = here / '.cache' / (f + '.pdf')
    L = lines(pdf, 9.5 if slug == 'anti-terrorism' else 11.4)
    cut = max(i for i, l in enumerate(L) if re.fullmatch(r'CHAPTER \d+[A-Z]?', l))
    B = L[cut:]
    pos, last = [], (0, '')
    for k, t in enumerate(B):
        m = re.match(r'^(\d+)([A-Z]{0,2})\.(?!\d)', t)
        if not m: continue
        i, le = int(m.group(1)), m.group(2)
        if (i == last[0] + 1 and not le) or (i == last[0] and le and le > last[1]):
            pos.append((m.group(1) + le, k)); last = (i, le)
    toc = [n for n, _ in pos]
    units = {}
    for idx, (n, j) in enumerate(pos):
        end = pos[idx + 1][1] if idx + 1 < len(pos) else len(B)
        paras, cur = [], ''
        for t in B[j:end]:
            if re.fullmatch(r'P [IVX]+|[A-Z][A-Z ,\-]{4,}', t):
                continue
            if not cur or re.match(r'^\(\w+\)', t) or t[0] in '"“':
                if cur: paras.append(cur)
                cur = t
            else:
                cur = cur[:-1] + t if cur.endswith('-') else cur + ' ' + t
        if cur: paras.append(cur)
        paras[0] = re.sub(r'^' + n + r'\.\s*', '', paras[0]) or paras[0]
        paras = [re.sub(r'^(\(\w+\))(?=\S)', lambda m: m.group(1) + ' ', x) for x in paras]
        key = 'sec-%03d%s' % (int(re.match(r'\d+', n).group()), re.sub(r'\d+', '', n).lower())
        units[key] = {'label': 'Section ' + n, 'kind': 'sec', 'text': '# Section %s\n' % n + '\n'.join(p for p in paras if p) + '\n'}
    return {'slug': slug, 'short': short, 'title': title, 'url': BASE + f + '.pdf', 'first_law': None, 'earlier_laws': [],
            'versions': [{'from': '2022-08-11', 'source_url': BASE + f + '.pdf', 'sha256': hashlib.sha256(pdf.read_bytes()).hexdigest(),
                          'units': units, 'credits': {}}]}, len(toc), len(units)

if __name__ == '__main__':
    acts = []
    for a in ACTS:
        act, nt, nu = parse(*a); print(a[0], 'toc', nt, 'units', nu); acts.append(act)
    corpus = {
     'country': {'code': 'BB', 'name': 'Barbados', 'slug': 'barbados', 'lang': 'en', 'tz': 'America/Barbados', 'future_branch': 'future',
       'publisher': {'name': 'Supreme Court Registry, Barbados Law Courts (Laws of Barbados)', 'email': 'laws@barbadoslawcourts.gov.bb.invalid'},
       'default_in_force_rule': {'text': 'No dated history is published. Each Act is one oldest-version-available commit dated 2022-08-11, the Last-Modified date of the published PDF; the Act commencement dates in the texts are not applied.', 'source': BASE},
       'licence_note': 'Text from the Laws of Barbados as published by the Barbados Law Courts (barbadoslawcourts.gov.bb), Government of Barbados. The site states no licence; the text is copied for reference with attribution to the publisher.'},
     'sources': [{'name': 'Barbados Law Courts: Statutes of Barbados (consolidated laws)', 'url': 'https://www.barbadoslawcourts.gov.bb/laws/consolidated-laws/statutes-of-barbados/', 'retrieved': '2026-10-29', 'requests': 5,
       'licence': 'no licence stated', 'notes': 'Born-digital PDFs only. The older scanned Acts (including the Constitution and the Interpretation Act) have only an OCR text layer and were not used.'}],
     'laws': {}, 'applies': [], 'acts': acts,
     'decisions': ['Three Acts were chosen because their PDFs are born-digital (Acrobat Distiller): Computer Misuse Cap. 124B, Anti-Terrorism Cap. 158 and Bail Cap. 122A. The Constitution, Citizenship and Interpretation PDFs are scans with an incomplete OCR layer and were not used (no OCR).',
       'Sections are split by sequential section number; margin notes, footnotes, page headers and italic sub-headings are dropped; schedules, where present, stay at the end of the last section.',
       'Version date 2022-08-11 is the Last-Modified header of each PDF (the source gives no consolidation date in the text beyond the L.R.O. year).'],
     'ai_use': ['Claude Code wrote the parser; it did not write or alter any legal text. 0 model calls at data-build time.']}
    (here / 'corpus.json').write_text(json.dumps(corpus, ensure_ascii=False, indent=1) + chr(10), encoding='utf8', newline=chr(10))
