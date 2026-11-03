"""Barbados: rewrite repo/README.md's table of Acts (between <!-- acts:start --> and <!-- acts:end -->) from
corpus.json and the verified parts (corpus.d/*.json with a .PUBLISH). Deterministic, no network.

    python -X utf8 bb_docs.py
"""
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent


def acts():
    out = json.loads((HERE / 'corpus.json').read_text('utf-8'))['acts']
    for p in sorted((HERE / 'corpus.d').glob('*.json')) if (HERE / 'corpus.d').exists() else []:
        if p.with_suffix('.PUBLISH').exists():
            out += json.loads(p.read_text('utf-8'))['acts']
    return out


def main():
    rows = ['| Folder | Act | Versions | Dated |', '| --- | --- | ---: | --- |']
    for a in sorted(acts(), key=lambda a: a['slug']):
        v = a['versions'][0]
        how = 'commencement (never amended in this edition)' if a.get('first_law') else 'oldest version available'
        rows.append(f"| `{a['slug']}/` | {a['title']} | {len(a['versions'])} | {v['from']}, {how} |")
    p = HERE / 'repo' / 'README.md'
    s = p.read_text('utf-8')
    table = '<!-- acts:start -->\n' + '\n'.join(rows) + '\n<!-- acts:end -->'
    if '<!-- acts:start -->' in s:
        s = re.sub(r'<!-- acts:start -->.*?<!-- acts:end -->', lambda m: table, s, flags=re.S)
    else:
        s = re.sub(r'\| Folder \| Act \|.*?\n\n', lambda m: table + '\n\n', s, count=1, flags=re.S)
    p.write_text(s, 'utf-8', newline='\n')
    print(len(rows) - 2, 'acts in README')


if __name__ == '__main__':
    main()
