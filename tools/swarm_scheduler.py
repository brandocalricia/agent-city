#!/usr/bin/env python3
"""Print a lane plan from data/omniroute.json. Free first; Grok is fallback percent only.

Does not call a model and does not start processes. One lane per pool. Local only while
remote free pools are down. Grok only when every free pool is out.
"""
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(os.path.dirname(HERE), "data", "omniroute.json")


def load(path=None):
    p = path or SRC
    try:
        with open(p, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def activity(data, remote):
    """Worker cap from free-provider headroom. Does not start processes.

    full: 2 or more remote free providers, workers = that count capped at 3.
    shifted: exactly one, workers = 1.
    minimal: none, workers = 0.
    An explicit mode on the snapshot wins when it is one of those three.
    """
    named = data.get("mode")
    if named in ("full", "shifted", "minimal"):
        workers = data.get("workers")
        if not isinstance(workers, int):
            workers = {"full": min(3, remote), "shifted": 1, "minimal": 0}[named]
        return named, workers
    if remote >= 2:
        return "full", min(3, remote)
    if remote == 1:
        return "shifted", 1
    return "minimal", 0


def plan(data):
    """Lane plan: free first, grok fallback percent only. Never starts workers."""
    lanes = data.get("lanes") if isinstance(data.get("lanes"), dict) else {}
    local = int(lanes.get("local") or 0)
    remote = int(lanes.get("remote_free") or 0)
    assigned = []
    if remote > 0:
        assigned.append({"pool": "remote_free", "lanes": min(remote, 3), "kind": "free"})
    elif local > 0:
        assigned.append({"pool": "local", "lanes": 1, "kind": "free"})
    free_lanes = sum(a["lanes"] for a in assigned)
    mode, workers = activity(data, remote)
    return {
        "assigned": assigned,
        "free_lanes": free_lanes,
        "grok_fallback_pct": 0 if free_lanes else 100,
        "mode": mode,
        "workers": workers,
        "next_reset": data.get("next_reset") or "none",
        "started": 0,
    }


def main():
    p = plan(load())
    print("lane plan (print only; no processes started)")
    if p["assigned"]:
        for a in p["assigned"]:
            print(f"  {a['kind']} {a['pool']}: {a['lanes']} lane")
    else:
        print("  no free lanes up")
    print(f"  grok fallback: {p['grok_fallback_pct']}%")
    print(f"  mode: {p['mode']} workers: {p['workers']} next reset: {p['next_reset']}")
    print(f"  workers started: {p['started']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
