"""Shared test helpers (stdlib only). Run the suite: python3 -m unittest discover -s tests -v"""
import hashlib, os, shutil, subprocess, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GB = os.path.join(ROOT, "grok-build")
BASH = "/bin/bash"  # macOS: bash 3.2, the version the owner's hook runs with
sys.path.insert(0, GB)
sys.path.insert(0, ROOT)

GOOD_GB = {"change": "Add a short global rule that says something useful for tests.", "target": "global", "size": "Quick",
           "why": "Because tests need a realistic item.", "checks": ["$ test -d {repo}", "No duplicate guidance exists"],
           "tests": ["$ grep -q '^## {id}' {rules_file}"]}


def sha(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def make_raw(dst):
    """A file:// copy of the repo files the installer reads, so tests can corrupt them."""
    os.makedirs(dst, exist_ok=True)
    shutil.copytree(GB, os.path.join(dst, "grok-build"))
    shutil.copy(os.path.join(ROOT, "IDEALS.md"), dst)
    rewrite_manifest(dst)  # install tests check logic; RepoState checks the committed manifest is fresh
    return "file://" + dst


def rewrite_manifest(raw_dir):
    """Recompute manifest.txt in a raw copy after a test changes a file there."""
    p = os.path.join(raw_dir, "grok-build", "manifest.txt")
    lines = [l.rstrip("\n") for l in open(p) if l.strip()]
    out = []
    for l in lines:
        parts = l.split("  ", 1)
        if len(parts) == 2 and len(parts[0]) == 64:
            out.append(f"{sha(os.path.join(raw_dir, parts[1]))}  {parts[1]}")
        else:
            out.append(l)
    open(p, "w").write("\n".join(out) + "\n")


def env(home, raw):
    e = dict(os.environ, HOME=home, GROK_HOME=os.path.join(home, ".grok"), AGENT_CITY_RAW=raw)
    e.update(GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@example.invalid", GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@example.invalid")
    return e


def run(cmd, e, cwd=None, input=None):
    return subprocess.run(cmd, env=e, cwd=cwd, input=input, capture_output=True, text=True)


class TempDir:
    def __enter__(self):
        self.d = os.path.realpath(tempfile.mkdtemp(prefix="agent-city-test-"))
        return self.d

    def __exit__(self, *a):
        shutil.rmtree(self.d, ignore_errors=True)
