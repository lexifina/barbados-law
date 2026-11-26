"""Every ~15 minutes: append newly fetched instruments to barbados-law main in batches of 300 commits (bb_build.py),
push fast-forward only after each batch, verify with ls-remote; then refresh data/held.json. One build/push at a time.
Stop: touch state/ship.stop."""
import os, sys, subprocess, time
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.join(os.path.dirname(ROOT), "barbados-law-pub")
LOG = os.path.join(ROOT, "progress.log")
NOWIN = 0x08000000
GIT = ["git", "-C", REPO]
ENV = {**os.environ, "PYTHONIOENCODING": "utf8"}


def log(m):
    with open(LOG, "a", encoding="utf8") as f:
        f.write(time.strftime("%Y-%m-%d %H:%M:%S ") + "ship " + m + "\n")


def run(*a, **k):
    return subprocess.run(a, capture_output=True, text=True, encoding="utf-8", errors="replace", creationflags=NOWIN, **k)


def push():
    p = run(*GIT, "push", "-q", "origin", "main")
    loc = run(*GIT, "rev-parse", "main").stdout.strip()
    rem = run(*GIT, "ls-remote", "origin", "refs/heads/main").stdout.split()
    log(f"push {'OK' if rem and rem[0] == loc else 'MISMATCH'} {loc[:10]} {p.stderr.strip()[-160:]}")
    return rem and rem[0] == loc


while True:
    if os.path.exists(os.path.join(ROOT, "state", "ship.stop")):
        log("stop file"); break
    shipped = False
    r = None
    while True:
        r = run(sys.executable, "-I", os.path.join(ROOT, "tools", "bb_build.py"), REPO, "--limit", "300", env=ENV)
        log("build: " + (r.stdout.strip() or r.stderr.strip()[-300:]))
        if not ("committed" in r.stdout and "fast-import rc 0" in r.stdout):
            break
        if not push():
            break
        shipped = True
        if "committed 300;" not in r.stdout:
            break
    src = os.path.join(ROOT, "held.json")
    if shipped and os.path.exists(src):
        old = run(*GIT, "show", "main:data/held.json").stdout
        if open(src, encoding="utf8").read().replace("\r\n", "\n") != old:
            run(sys.executable, "-I", os.path.join(ROOT, "tools", "commit_files.py"), REPO,
                "data/held.json: instruments held back (no usable text layer, no date found, duplicate or not fetched)",
                f"data/held.json={src}", env=ENV)
            push()
    done = open(LOG, encoding="utf8").read()
    if "fetch DONE" in done and r is not None and "nothing new" in r.stdout:
        log("all fetched and shipped"); break
    time.sleep(900)
