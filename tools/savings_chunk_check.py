#!/usr/bin/env python3
"""Fail if an upgrade wipes the Savings line. Re-apply only onto the pre-patch file."""

import json
import os
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

BACKUP = Path.home() / ".agent-city" / "backup"
GOOD = BACKUP / "savings-good"
DIST = Path(
    os.environ.get(
        "OMNIROUTE_DIST",
        "/opt/homebrew/lib/node_modules/omniroute/dist",
    )
)
STAMP = "20261009T235429Z"


def target(name, relative, markers, kind, backup_name=None):
    item = {
        "name": name,
        "live": DIST / relative,
        "markers": markers,
        "kind": kind,
        "good": GOOD / name,
    }
    if backup_name:
        item["pre"] = BACKUP / backup_name
    return item


TARGETS = [
    target(
        "costs-page",
        ".build/next/static/chunks/b9costs-e.js",
        ("Savings $", "as of"),
        "created",
    ),
    target(
        "costs-client",
        ".build/next/static/chunks/0x1yty8y_3k4a.js",
        ("Savings $", "as of"),
        "patched",
        f"0x1yty8y_3k4a.js.bak-b9stats4-{STAMP}",
    ),
    target(
        "costs-ssr",
        ".build/next/server/chunks/ssr/src_app_(dashboard)_dashboard_costs_0d727w7._.js",
        ("Savings $", "as of"),
        "patched",
        f"src_app_(dashboard)_dashboard_costs_0d727w7._.js.bak-b9stats4-{STAMP}",
    ),
    target(
        "analytics-api",
        ".build/next/server/chunks/_1xj06si._.js",
        ("ef.savings=ef.totalCost", "ef.asOf=ef.lastRequest"),
        "patched",
        f"_1xj06si._.js.bak-b9stats4-{STAMP}",
    ),
    target(
        "costs-manifest",
        ".build/next/server/app/(dashboard)/dashboard/costs/page_client-reference-manifest.js",
        ("b9costs-e.js",),
        "patched",
        f"page_client-reference-manifest.js.bak-b9stats4-{STAMP}",
    ),
]


def has_markers(text, markers):
    return all(marker in text for marker in markers)


def decide(kind, exists, marked, same_as_pre, good_exists):
    """ok, reapply, or fail. Never overwrite a file an upgrade replaced."""
    if exists and marked:
        return "ok"
    if kind == "created" and not exists and good_exists:
        return "reapply"
    if kind == "patched" and exists and (not marked) and same_as_pre and good_exists:
        return "reapply"
    return "fail"


def save_good():
    GOOD.mkdir(parents=True, exist_ok=True)
    saved = []
    for item in TARGETS:
        live = item["live"]
        if not live.is_file():
            continue
        text = live.read_text(errors="replace")
        if not has_markers(text, item["markers"]):
            continue
        shutil.copy2(live, item["good"])
        saved.append(item["name"])
    return saved


def check_one(item, apply):
    live = item["live"]
    exists = live.is_file()
    marked = False
    if exists:
        marked = has_markers(live.read_text(errors="replace"), item["markers"])
    same_as_pre = False
    pre = item.get("pre")
    if exists and pre and pre.is_file():
        same_as_pre = live.read_bytes() == pre.read_bytes()
    action = decide(
        item["kind"],
        exists,
        marked,
        same_as_pre,
        item["good"].is_file(),
    )
    if action == "reapply" and apply:
        live.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(item["good"], live)
        marked = has_markers(live.read_text(errors="replace"), item["markers"])
        action = "reapplied" if marked else "fail"
    return action


def write_proof(ok, failed):
    proof = Path.home() / ".agent-city" / "proofs" / "savings-chunk.json"
    proof.parent.mkdir(parents=True, exist_ok=True)
    handle = os.open(str(proof), os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    try:
        body = {
            "ok": ok,
            "failed": failed,
            "checkedAt": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
        os.write(handle, (json.dumps(body, indent=2) + "\n").encode())
    finally:
        os.close(handle)


def main(argv):
    if "--save-good" in argv:
        saved = save_good()
        print("savings-good " + ",".join(saved))
        return 0 if len(saved) == len(TARGETS) else 1
    apply = "--check-only" not in argv
    failed = []
    reapplied = []
    for item in TARGETS:
        action = check_one(item, apply)
        if action == "fail":
            failed.append(item["name"])
        elif action == "reapplied":
            reapplied.append(item["name"])
    try:
        write_proof(not failed, failed)
    except Exception:
        print("savings-chunk fail: check-error")
        return 1
    if failed:
        print("savings-chunk fail: " + ",".join(failed))
        return 1
    if reapplied:
        print("savings-chunk reapplied: " + ",".join(reapplied))
        return 0
    print("savings-chunk ok")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except Exception:
        print("savings-chunk fail: check-error")
        sys.exit(1)
