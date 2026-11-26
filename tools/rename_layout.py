"""One-off: move the flat <slug>/ Act folders of barbados-law into revised-laws/cap-NNN-<slug>/ (pure renames).
python -I tools/rename_layout.py <repo> [--dry]"""
import re, subprocess, sys, os

repo = sys.argv[1]
git = lambda *a: subprocess.run(["git", "-C", repo, *a], capture_output=True, text=True, encoding="utf-8", check=True).stdout
log = git("log", "--format=@@%n%(trailers:key=Consolidated,valueonly)%(trailers:key=Source,valueonly)", "--name-only", "main")
caps = {}
for block in log.split("@@")[1:]:
    lines = [x.strip() for x in block.strip().split("\n") if x.strip()]
    urls = [x for x in lines if x.startswith("http")]
    files = [x for x in lines if not x.startswith("http")]
    folders = {f.split("/")[0] for f in files if "/" in f}
    for u in urls:
        m = re.search(r"CAP\.?\s*(\d+)([A-Z]*)\.pdf$", u.replace("%20", " "), re.I)
        if m:
            for fo in folders:
                caps.setdefault(fo, f"{int(m.group(1)):03d}{m.group(2).lower()}")
top = [x for x in git("ls-tree", "-d", "--name-only", "main").split() if x]
keep = {"data", "tools", "visualisations", "vulnerabilities", "revised-laws", "acts", "subsidiary", "constitution"}
moves = []
for fo in top:
    if fo in keep:
        continue
    cap = caps.get(fo)
    if not cap:
        print("NO CAP", fo); continue
    slug = re.sub(r"-cap-\d+[a-z]*$", "", fo)
    moves.append((fo, f"revised-laws/cap-{cap}-{slug}"))
dst = [d for _, d in moves]
assert len(dst) == len(set(dst)), "duplicate destination"
for a, b in moves:
    print(a, "->", b)
print(len(moves), "moves")
if "--dry" not in sys.argv:
    mp = dict(moves)
    lines = []
    for ln in git("ls-tree", "-r", "--full-tree", "main").splitlines():
        meta, path = ln.split("\t", 1)
        head, _, rest = path.partition("/")
        lines.append(meta + "\t" + (mp[head] + "/" + rest if head in mp and rest else path))
    msg = ("Move the Act folders into revised-laws/cap-NNN-<slug>/ (renames only, no text changed)\n\n"
           "Each of the 122 consolidated Acts moves from <slug>/ to revised-laws/cap-NNN-<slug>/, NNN being its chapter\n"
           "number in the Laws of Barbados. Nothing else changes in this commit.\n")
    import time
    when = f"{int(time.time())} +0000"
    fi = "commit refs/heads/main\n" + f"author Lexifina <barbados-law@lexifina.com> {when}\ncommitter Lexifina <barbados-law@lexifina.com> {when}\n"
    mb = msg.encode("utf-8")
    parent = git("rev-parse", "main").strip()
    body = [f"from {parent}", "deleteall"]
    for ln in lines:
        meta, path = ln.split("\t", 1)
        mode, typ, sha = meta.split()
        body.append(f"M {mode} {sha} {path}")
    data = fi.encode() + f"data {len(mb)}\n".encode() + mb + ("\n".join(body) + "\n\ndone\n").encode("utf-8")
    subprocess.run(["git", "-C", repo, "fast-import", "--quiet", "--done"], input=data, check=True)
    print("commit", git("rev-parse", "main").strip())
