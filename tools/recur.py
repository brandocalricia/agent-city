#!/usr/bin/env python3
"""Run the b9recur1 probes that are ready.

A plain run and --minute do the same no-key work. --minute is what the
runner's minute self-heal calls. Other b9recur1 cases stay open and are
not printed as PASS.
"""

import fcntl
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OMNI = Path("/opt/homebrew/lib/node_modules/omniroute")
FAKES = ("fake-nokey-b9errrows3", "fake-lostkey-b9errrows4")


def run(cmd, cwd):
    proc = subprocess.run(cmd, cwd=str(cwd), text=True)
    return proc.returncode


def cleanup_fakes():
    """Remove only the two fake providers this probe creates."""
    db = Path.home() / ".omniroute" / "storage.sqlite"
    if not db.is_file():
        return
    names = ",".join("'" + name + "'" for name in FAKES)
    subprocess.run(
        [
            "sqlite3",
            str(db),
            f"DELETE FROM provider_connections WHERE provider IN ({names});",
        ],
        check=False,
        capture_output=True,
        text=True,
    )


def take_lock():
    path = Path.home() / ".agent-city" / ".nokey-heal.lock"
    path.parent.mkdir(parents=True, exist_ok=True)
    handle = open(path, "a")
    try:
        fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        handle.close()
        print("nokey heal busy")
        return None
    return handle


def nokey():
    code = run([sys.executable, str(ROOT / "tools" / "reapply_nokey.py")], ROOT)
    if code != 0:
        return code
    launcher = OMNI / "node_modules" / "tsx" / "dist" / "cli.mjs"
    test = ROOT / "tests" / "run_add_nokey.mjs"
    if not launcher.is_file() or not test.is_file():
        print("FAIL nokey test launcher missing")
        return 1
    code = run(["node", str(launcher), str(test)], OMNI)
    cleanup_fakes()
    return code


def main(argv):
    extra = [arg for arg in argv[1:] if arg != "--minute"]
    if extra:
        print("FAIL unknown recur argument")
        return 1
    lock = take_lock()
    if lock is None:
        return 0
    try:
        code = nokey()
        if code == 0:
            print("PASS recur ran reapply_nokey.py and add_nokey_provider.mjs")
        return code
    finally:
        fcntl.flock(lock, fcntl.LOCK_UN)
        lock.close()


if __name__ == "__main__":
    sys.exit(main(sys.argv))
