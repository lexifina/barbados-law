"""Commit local files into a repo's main without a checkout (the publish clone is sparse).
python -I tools/commit_files.py <repo> "<message>" <repo/path>=<local file> [...]   (local file '-' deletes the path)"""
import subprocess, sys, time

repo, msg = sys.argv[1], sys.argv[2]
parent = subprocess.run(["git", "-C", repo, "rev-parse", "main"], capture_output=True, text=True, check=True).stdout.strip()
when = f"{int(time.time())} +0000"
out = [b"commit refs/heads/main\n",
       f"author Lexifina <barbados-law@lexifina.com> {when}\ncommitter Lexifina <barbados-law@lexifina.com> {when}\n".encode()]
m = msg.encode("utf-8")
out += [f"data {len(m)}\n".encode(), m, b"\n", f"from {parent}\n".encode()]
for spec in sys.argv[3:]:
    path, _, local = spec.partition("=")
    if local == "-":
        out.append(f"D {path}\n".encode("utf-8")); continue
    b = open(local, "rb").read().replace(b"\r\n", b"\n")
    out += [f"M 100644 inline {path}\n".encode("utf-8"), f"data {len(b)}\n".encode(), b, b"\n"]
out.append(b"\ndone\n")
subprocess.run(["git", "-C", repo, "fast-import", "--quiet", "--done"], input=b"".join(out), check=True, creationflags=0x08000000)
print(subprocess.run(["git", "-C", repo, "rev-parse", "main"], capture_output=True, text=True).stdout.strip())
