#!/usr/bin/env python3
"""Fail if publishable files contain private patterns (emails, $amounts with sender-ish context).
Optimizer 2026-10-08 evening: cheap pre-publish gate for R-006; run from tests and before push.
Exit 0 = clean, 1 = hits found (prints paths). Local-only files are skipped.
"""
import os, re, sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKIP_NAMES = {
    "private.json", "private.js", "budget.json", "channel-seen.json", "requests.json",
    ".gitignore",
}
SKIP_DIRS = {".git", "screenshots", "__pycache__", "archive", "node_modules"}
# Emails + dollar amounts that look like money (not code versions)
EMAIL_RE = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I)
# Allow github noreply / example.com in workflows and docs about bots
ALLOW_EMAIL_SUBSTR = (
    "users.noreply.github.com",
    "github.com",
    "example.com",
    "example.invalid",  # RFC 2606 test TLD used in suite git env
    "noreply@",
)
ALLOW_EMAIL_SUFFIXES = (".invalid", ".example", ".test")
AMOUNT_RE = re.compile(r"\$\d{1,3}(?:,\d{3})+(?:\.\d{2})?|\b(?:owed|due|invoice|payment)\b.{0,40}\$\d+", re.I)

def iter_files(root):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not d.startswith(".")]
        for name in filenames:
            if name in SKIP_NAMES or name.endswith((".png", ".jpg", ".webp", ".gif", ".pyc", ".zip")):
                continue
            yield os.path.join(dirpath, name)

def check_text(path, text):
    hits = []
    for m in EMAIL_RE.finditer(text):
        s = m.group(0)
        low = s.lower()
        if any(a in low for a in ALLOW_EMAIL_SUBSTR):
            continue
        if any(low.endswith(suf) for suf in ALLOW_EMAIL_SUFFIXES):
            continue
        hits.append(f"email:{s}")
    for m in AMOUNT_RE.finditer(text):
        hits.append(f"amount:{m.group(0)[:40]}")
    return hits

def main(argv=None):
    root = HERE
    bad = []
    for path in iter_files(root):
        try:
            with open(path, encoding="utf-8", errors="replace") as fh:
                text = fh.read()
        except OSError:
            continue
        hits = check_text(path, text)
        if hits:
            bad.append((os.path.relpath(path, root), hits[:5]))
    if bad:
        for p, hits in bad:
            print(f"PRIVACY: {p}: {', '.join(hits)}")
        return 1
    print("privacy_check: clean")
    return 0

if __name__ == "__main__":
    sys.exit(main())
