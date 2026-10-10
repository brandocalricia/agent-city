#!/usr/bin/env python3
"""Reapply the no-key inactive patch onto an OmniRoute install.

Prints PASS lines when the install already has every guard. Applies
patches/omniroute-nokey-inactive.patch when any guard is missing.
Checks all three markers before and after patching. Exits 1 with a
FAIL line when any marker is still missing after that.

REAPPLY_NOKEY_PATCH overrides the patch file for tests.
"""

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATCH = ROOT / "patches" / "omniroute-nokey-inactive.patch"
DEFAULT = Path("/opt/homebrew/lib/node_modules/omniroute")
MARKER = "export function unkeyedApikeyConnection"
LOST = "A stored key that is cleared must leave the combo set"
ACTIVE0 = "connection.isActive === false || connection.isActive === 0"
FAIL = "FAIL installed OmniRoute is missing unkeyedApikeyConnection"


def read_text(path):
    if not path.is_file():
        return ""
    return path.read_text(errors="replace")


def guard_present(install):
    """True only when the function, the lost-key clear, and the numeric skip exist."""
    providers = read_text(install / "src" / "lib" / "db" / "providers.ts")
    observe = read_text(install / "src" / "lib" / "monitoring" / "observability.ts")
    return MARKER in providers and LOST in providers and ACTIVE0 in observe


def patch_file():
    override = os.environ.get("REAPPLY_NOKEY_PATCH", "").strip()
    if override:
        return Path(override)
    return PATCH


def report(kind):
    print(f"PASS reapply {kind} unkeyedApikeyConnection")
    print(f"PASS reapply {kind} the lost-key combo clear")
    print(f"PASS reapply {kind} the numeric inactive error skip")


def main():
    install = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT
    providers = install / "src" / "lib" / "db" / "providers.ts"
    if not providers.is_file():
        print(FAIL)
        return 1
    if guard_present(install):
        report("found")
        return 0
    patch = patch_file()
    if not patch.is_file():
        print(FAIL)
        return 1
    proc = subprocess.run(
        ["patch", "-d", str(install), "-p1", "--forward", "--batch"],
        input=patch.read_text(),
        text=True,
        capture_output=True,
    )
    if proc.returncode != 0 or not guard_present(install):
        print(FAIL)
        return 1
    report("installed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
