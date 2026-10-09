"""The no-key reapply checks all three markers before and after patching."""

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import reapply_nokey  # noqa: E402

SCRIPT = ROOT / "tools" / "reapply_nokey.py"
LIVE = Path("/opt/homebrew/lib/node_modules/omniroute")
MARKER = reapply_nokey.MARKER
LOST = reapply_nokey.LOST
ACTIVE0 = reapply_nokey.ACTIVE0


def write_tree(root, providers, observe):
    db = root / "src" / "lib" / "db"
    mon = root / "src" / "lib" / "monitoring"
    db.mkdir(parents=True)
    mon.mkdir(parents=True)
    (db / "providers.ts").write_text(providers)
    (mon / "observability.ts").write_text(observe)


def run_cli(install, patch=None):
    env = os.environ.copy()
    if patch is not None:
        env["REAPPLY_NOKEY_PATCH"] = str(patch)
    return subprocess.run(
        [sys.executable, str(SCRIPT), str(install)],
        capture_output=True,
        text=True,
        env=env,
    )


def noop_patch(path, context):
    body = [f"@@ -1,{len(context)} +1,{len(context)} @@"]
    for line in context[:-1]:
        body.append(" " + line)
    body.append("-" + context[-1])
    body.append("+seeded")
    path.write_text(
        "\n".join(
            [
                "diff -ruN a/src/lib/db/providers.ts b/src/lib/db/providers.ts",
                "--- a/src/lib/db/providers.ts",
                "+++ b/src/lib/db/providers.ts",
                *body,
                "",
            ]
        )
    )


def test_found_requires_all_three():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_tree(root, MARKER + "\n" + LOST + "\nseed\n", "if (" + ACTIVE0 + ") continue;\n")
        proc = run_cli(root)
        assert proc.returncode == 0, proc.stdout + proc.stderr
        assert "PASS reapply found unkeyedApikeyConnection" in proc.stdout
        assert "PASS reapply found the lost-key combo clear" in proc.stdout
        assert "PASS reapply found the numeric inactive error skip" in proc.stdout
        assert "installed" not in proc.stdout
    print("PASS reapply accepts an install only when all three markers are already present")


def test_missing_lost_fails():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_tree(root, MARKER + "\nseed\n", "if (" + ACTIVE0 + ") continue;\n")
        patch = root / "noop.diff"
        noop_patch(patch, [MARKER, "seed"])
        proc = run_cli(root, patch)
        assert proc.returncode == 1, proc.stdout + proc.stderr
        assert proc.stdout.strip() == reapply_nokey.FAIL
        text = (root / "src" / "lib" / "db" / "providers.ts").read_text()
        assert "seeded" in text
        assert LOST not in text
    print("PASS reapply fails when the lost-key line is still missing after the patch")


def test_missing_active0_fails():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_tree(root, MARKER + "\n" + LOST + "\nseed\n", "if (connection.isActive === false) continue;\n")
        patch = root / "noop.diff"
        noop_patch(patch, [MARKER, LOST, "seed"])
        proc = run_cli(root, patch)
        assert proc.returncode == 1, proc.stdout + proc.stderr
        assert proc.stdout.strip() == reapply_nokey.FAIL
        providers = (root / "src" / "lib" / "db" / "providers.ts").read_text()
        observe = (root / "src" / "lib" / "monitoring" / "observability.ts").read_text()
        assert "seeded" in providers
        assert ACTIVE0 not in observe
    print("PASS reapply fails when the numeric inactive line is still missing after the patch")


def test_reverse_then_reapply():
    if not (LIVE / "src" / "lib" / "db" / "providers.ts").is_file():
        print("FAIL live OmniRoute tree missing")
        return 1
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        for rel in (
            "src/lib/db/providers.ts",
            "src/lib/monitoring/observability.ts",
        ):
            dest = root / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(LIVE / rel, dest)
        reverse = subprocess.run(
            ["patch", "-d", str(root), "-p1", "-R", "--batch"],
            input=(ROOT / "patches" / "omniroute-nokey-inactive.patch").read_text(),
            text=True,
            capture_output=True,
        )
        assert reverse.returncode == 0, reverse.stdout + reverse.stderr
        wiped = (root / "src" / "lib" / "db" / "providers.ts").read_text()
        assert MARKER not in wiped
        assert LOST not in wiped
        proc = run_cli(root)
        assert proc.returncode == 0, proc.stdout + proc.stderr
        restored_p = (root / "src" / "lib" / "db" / "providers.ts").read_text()
        restored_o = (root / "src" / "lib" / "monitoring" / "observability.ts").read_text()
        assert MARKER in restored_p
        assert LOST in restored_p
        assert ACTIVE0 in restored_o
        assert "PASS reapply installed unkeyedApikeyConnection" in proc.stdout
        assert "PASS reapply installed the lost-key combo clear" in proc.stdout
        assert "PASS reapply installed the numeric inactive error skip" in proc.stdout
    print("PASS reapply restores all three markers on a wiped tree")
    return 0


def main():
    test_found_requires_all_three()
    test_missing_lost_fails()
    test_missing_active0_fails()
    if test_reverse_then_reapply() != 0:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
