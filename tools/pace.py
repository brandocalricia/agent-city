#!/usr/bin/env python3
"""Weekly Grok Bot usage pacing for Agent City sessions (stdlib only, deterministic).

Reads budget.json (local only, gitignored) when present and prints ONLY numbers and times:
estimated used %, remaining % to the target, hours and scheduled sessions left before the reset,
and the recommended size for THIS session. Task descriptions ("what"/"task") are never printed.

  python3 tools/pace.py            # human-readable
  python3 tools/pace.py --json     # machine-readable (same numbers)
  python3 tools/pace.py --now 2026-10-08T08:49 --budget path/to/budget.json

Estimated used % = latest real reading (from the owner's Usage page) + every logged session and
ad-hoc entry after that reading (est_pct, or calibration.pct_per_tier[tier]).
Every session must also log its own entry in budget.json "sessions" when it finishes, and ad-hoc
work the owner asks Grok Bot for goes in "adhoc", so the next session recalculates.
"""
import argparse
import datetime as dt
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_BUDGET = os.path.join(os.path.dirname(HERE), "budget.json")
TIERS = ("L", "M", "S")
DEFAULT_TIER_PCT = {"S": 0.75, "M": 1.5, "L": 2.5}
DEFAULT_SLOTS = ["02:49", "05:49", "08:49", "11:49", "14:49", "17:49", "20:49", "23:49"]  # the every-3-hours routine
OVER_PACE_MINIMAL = 25.0   # points above the straight-line pace: at most a minimal session
OVER_PACE_SKIP = 40.0      # points above pace: skip (log a one-line skip)


def parse_t(s):
    return dt.datetime.strptime(str(s)[:16], "%Y-%m-%dT%H:%M")


def fmt(t):
    return t.strftime("%Y-%m-%dT%H:%M")


def entry_pct(e, tier_pct):
    for k in ("est_pct", "estimate_pct"):   # adhoc entries use est_pct, session entries estimate_pct
        if isinstance(e.get(k), (int, float)) and not isinstance(e.get(k), bool):
            return float(e[k])
    return float(tier_pct.get(str(e.get("tier", "")).upper(), 0.0))


def slots_between(start, end, slots):
    """Scheduled session start times in [start, end)."""
    n, day = 0, start.date()
    while dt.datetime.combine(day, dt.time()) < end:
        for s in slots:
            h, m = (int(x) for x in s.split(":"))
            t = dt.datetime.combine(day, dt.time(h, m))
            if start <= t < end:
                n += 1
        day += dt.timedelta(days=1)
    return n


def compute(budget, now):
    period = dt.timedelta(days=int(budget.get("reset_period_days", 7)))
    reset = parse_t(budget["reset_local"])
    rolled = 0
    while reset <= now:          # the stored reset is in the past: roll forward a period at a time
        reset += period
        rolled += 1
    start = reset - period
    tier_pct = dict(DEFAULT_TIER_PCT)
    tier_pct.update((budget.get("calibration") or {}).get("pct_per_tier") or {})
    target = float(budget.get("target_used_pct_at_reset", 97))
    readings = sorted((r for r in budget.get("readings", []) if isinstance(r, dict) and "at" in r and parse_t(r["at"]) <= now),
                      key=lambda r: parse_t(r["at"]))
    reading = readings[-1] if readings else None
    has_reading = bool(reading) and parse_t(reading["at"]) >= start
    if has_reading:
        base, since = float(reading["used_pct"]), parse_t(reading["at"])
    else:                        # no reading in this window (e.g. after a reset): start from 0 at the window start
        base, since = 0.0, start
    logged = [e for key in ("sessions", "adhoc") for e in budget.get(key, []) if isinstance(e, dict) and "at" in e]
    after = [e for e in logged if since < parse_t(e["at"]) <= now]
    added = round(sum(entry_pct(e, tier_pct) for e in after), 2)
    used = round(base + added, 2)
    hours_left = round((reset - now).total_seconds() / 3600, 1)
    reserve = float(budget.get("reserve_pct", 0))
    release_h = float(budget.get("reserve_release_hours_before_reset", 12))
    reserve_held = reserve if hours_left > release_h else 0.0
    remaining = round(target - used, 2)
    spendable = round(remaining - reserve_held, 2)
    slots = budget.get("session_times_local") or DEFAULT_SLOTS
    sessions_left = max(1, slots_between(now - dt.timedelta(minutes=30), reset, slots))  # includes this session
    per_session = round(spendable / sessions_left, 2)
    elapsed = (now - start).total_seconds() / period.total_seconds()
    pace_line = round(target * max(0.0, min(1.0, elapsed)), 1)
    over_pace = round(used - pace_line, 1)
    if per_session >= tier_pct["L"]:
        rec = "L"
    elif per_session >= tier_pct["M"]:
        rec = "M"
    elif per_session >= tier_pct["S"]:
        rec = "S"
    elif per_session >= tier_pct["S"] * 0.4:
        rec = "minimal"
    else:
        rec = "skip"
    order = ["skip", "minimal", "S", "M", "L"]
    if over_pace >= OVER_PACE_SKIP:
        rec = "skip"
    elif over_pace >= OVER_PACE_MINIMAL and order.index(rec) > order.index("minimal"):
        rec = "minimal"
    return {
        "now": fmt(now), "reset": fmt(reset), "reset_rolled_forward": rolled,
        "reading_pct": base, "reading_at": fmt(since) if has_reading else None,
        "logged_since_reading": len(after), "logged_pct_since_reading": added,
        "est_used_pct": used, "target_pct": target, "remaining_pct": remaining,
        "reserve_held_pct": reserve_held, "spendable_pct": spendable,
        "hours_left": hours_left, "sessions_left": sessions_left, "per_session_pct": per_session,
        "pace_line_pct": pace_line, "over_pace_pts": over_pace, "recommend": rec,
        "tier_pct": tier_pct,
    }


ADVICE = {
    "L": "full session: one solid increment plus all roles due",
    "M": "normal session: one modest increment, roles due",
    "S": "small session: Inspector, roles due, a polish-sized increment at most",
    "minimal": "minimal: Inspector check and roles strictly due today, no build work",
    "skip": "skip: log a one-line skip entry and stop",
}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--budget", default=DEFAULT_BUDGET)
    ap.add_argument("--now", help="local time YYYY-MM-DDTHH:MM (default: now in the budget's timezone)")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    if not os.path.exists(a.budget):
        print("pace: no budget.json (only on the owner's local copy); size the session as M")
        return 0
    try:
        with open(a.budget, encoding="utf-8") as f:
            budget = json.load(f)
        if a.now:
            now = parse_t(a.now)
        else:
            try:
                from zoneinfo import ZoneInfo
                now = dt.datetime.now(ZoneInfo(budget.get("timezone", "America/Denver"))).replace(tzinfo=None)
            except Exception:
                now = dt.datetime.now()
        r = compute(budget, now)
    except (ValueError, KeyError, TypeError) as e:
        print(f"pace: budget.json unreadable ({type(e).__name__}); size the session as S", file=sys.stderr)
        return 2
    if a.json:
        print(json.dumps(r, indent=1))
        return 0
    print(f"Pace at {r['now']} (local), reset {r['reset']}" + (f" (rolled forward {r['reset_rolled_forward']}x)" if r["reset_rolled_forward"] else ""))
    print(f"  estimated used: {r['est_used_pct']}% = reading {r['reading_pct']}%"
          + (f" at {r['reading_at']}" if r["reading_at"] else " (no reading this week)")
          + f" + {r['logged_pct_since_reading']}% from {r['logged_since_reading']} logged sessions/ad-hoc tasks since")
    print(f"  remaining to the {r['target_pct']:g}% target: {r['remaining_pct']}%"
          + (f" ({r['reserve_held_pct']:g}% reserve held until the last 12 h)" if r["reserve_held_pct"] else " (reserve released)"))
    print(f"  {r['hours_left']} h and {r['sessions_left']} scheduled sessions left -> {r['per_session_pct']}% per session")
    print(f"  straight-line pace now: {r['pace_line_pct']}% ({'+' if r['over_pace_pts'] >= 0 else ''}{r['over_pace_pts']} pts {'over' if r['over_pace_pts'] >= 0 else 'under'})")
    print(f"  recommend: {r['recommend']} ({ADVICE[r['recommend']]})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
