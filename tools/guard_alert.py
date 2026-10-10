#!/usr/bin/env python3
"""Post one Channel note when a standing guard flips to fail. Stay quiet when it passes."""

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

PROOFS = Path.home() / ".agent-city" / "proofs"
STATE = PROOFS / "guard-alert.json"
CHECKS = ("p0-settings.json", "savings-chunk.json")


def failure_signature():
    parts = []
    for name in CHECKS:
        path = PROOFS / name
        try:
            data = json.loads(path.read_text())
        except Exception:
            continue
        if not isinstance(data, dict) or data.get("ok") is not False:
            continue
        failed = data.get("failed")
        if not isinstance(failed, list):
            failed = ["failed"]
        clean = [str(item) for item in failed if isinstance(item, str)]
        parts.append(name.split(".")[0] + ":" + ",".join(clean or ["failed"]))
    return "|".join(parts)


def should_post(signature, last_signature):
    if not signature:
        return False
    return signature != last_signature


def post(signature):
    body = (
        "[from:grok-build] [id:gguard] [re:b9stats4ok]\n\n"
        "guard FAIL. " + signature.replace("|", ". ") + ".\n"
        "The minute heal is still running.\n"
    )
    payload = json.dumps({"body": body})
    proc = subprocess.run(
        [
            "gh",
            "api",
            "--method",
            "POST",
            "repos/brandocalricia/agent-city-comms/issues/1/comments",
            "--input",
            "-",
        ],
        input=payload,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    return proc.returncode == 0


def main():
    signature = failure_signature()
    try:
        last = json.loads(STATE.read_text())
    except Exception:
        last = {}
    last_signature = last.get("signature") if isinstance(last, dict) else ""
    if not isinstance(last_signature, str):
        last_signature = ""
    if not should_post(signature, last_signature):
        if not signature and last_signature:
            STATE.write_text(json.dumps({"signature": "", "postedAt": ""}) + "\n")
        print("guard quiet")
        return 0
    if not post(signature):
        print("guard alert not posted")
        return 0
    PROOFS.mkdir(parents=True, exist_ok=True)
    STATE.write_text(
        json.dumps(
            {
                "signature": signature,
                "postedAt": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            }
        )
        + "\n"
    )
    print("guard posted")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        print("guard alert not posted")
        sys.exit(0)
