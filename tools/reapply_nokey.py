#!/usr/bin/env python3
"""Reapply the no-key inactive patch onto an OmniRoute install.

Prints a PASS line when the install already has the guard. Applies
patches/omniroute-nokey-inactive.patch when the guard is missing.
Exits 1 with a FAIL line when the guard is still missing after that.
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATCH = ROOT / "patches" / "omniroute-nokey-inactive.patch"
DEFAULT = Path("/opt/homebrew/lib/node_modules/omniroute")
MARKER = "export function unkeyedApikeyConnection"
LOST = "A stored key that is cleared must leave the combo set"


def main():
    install = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT
    target = install / "src" / "lib" / "db" / "providers.ts"
    if not target.is_file():
        print("FAIL installed OmniRoute is missing unkeyedApikeyConnection")
        return 1
    text = target.read_text()
    if MARKER in text and LOST in text:
        print("PASS reapply found unkeyedApikeyConnection already in place")
        return 0
    if not PATCH.is_file():
        print("FAIL installed OmniRoute is missing unkeyedApikeyConnection")
        return 1
    proc = subprocess.run(
        ["patch", "-d", str(install), "-p1", "--forward", "--batch"],
        input=PATCH.read_text(),
        text=True,
        capture_output=True,
    )
    text = target.read_text()
    if proc.returncode != 0 or MARKER not in text:
        print("FAIL installed OmniRoute is missing unkeyedApikeyConnection")
        return 1
    print("PASS reapply installed unkeyedApikeyConnection")
    return 0


if __name__ == "__main__":
    sys.exit(main())
