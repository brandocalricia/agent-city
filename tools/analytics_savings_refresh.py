#!/usr/bin/env python3
"""Write the live Usage Analytics savings reading for the status line.

Reads the local gateway analytics summary and stores estimated cost, actual
spend, and savings. Free lanes use actual spend 0, so savings equals the
paid-equivalent cost. Never prints secrets.
"""

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

OUT = Path.home() / ".agent-city" / "proofs" / "analytics-savings.json"
FETCH = r"""
import { apiFetch } from "./bin/cli/api.mjs";
const res = await apiFetch("/api/usage/analytics");
if (!res.ok) process.exit(2);
const data = await res.json();
const s = data.summary || {};
process.stdout.write(JSON.stringify({
  estimatedCost: s.estimatedCost ?? s.totalCost ?? null,
  actualSpend: s.actualSpend ?? 0,
  savings: s.savings ?? null,
  asOf: s.asOf || s.lastRequest || "",
  requests: s.totalRequests ?? null,
}));
"""


def main() -> int:
    root = "/opt/homebrew/lib/node_modules/omniroute"
    proc = subprocess.run(
        ["node", "--input-type=module", "-e", FETCH],
        cwd=root,
        capture_output=True,
        text=True,
        timeout=30,
    )
    if proc.returncode != 0 or not proc.stdout.strip():
        return 1
    data = json.loads(proc.stdout)
    savings = data.get("savings")
    if isinstance(savings, bool) or not isinstance(savings, (int, float)):
        return 1
    data["fetchedAt"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    data["source"] = "usage analytics summary"
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(data, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(1)
