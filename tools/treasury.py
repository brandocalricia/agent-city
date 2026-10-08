"""Treasury numbers for data.js (stdlib only; imported by build_data.py).

Everything is derived from costs.json (the Meter Reader's measured ledger and the Optimizer's savings)
and, on the owner's local copy only, the weekly pacing numbers from tools/pace.py. Nothing is invented:
token figures are bytes / 4 estimates and dollar figures are API-equivalent estimates at the price
stated in costs.json "price". Lifetime totals = every ledger entry + costs.json "archived" (entries
removed later to keep the file small), so they keep accumulating week after week.
"""
import datetime as dt
import os

LEDGER_IN_DATA = 12   # data.js shows the newest 12 ledger entries; lifetime totals still count all of them


def _num(x):
    return x if isinstance(x, (int, float)) and not isinstance(x, bool) else 0


def lifetime(costs):
    led = [e for e in costs.get("ledger", []) if isinstance(e, dict)]
    arc = costs.get("archived") if isinstance(costs.get("archived"), dict) else {}
    out = {
        "sessions": len(led) + int(_num(arc.get("sessions"))),
        "kb_pushed": round(sum(_num(e.get("kb_pushed")) for e in led) + _num(arc.get("kb_pushed")), 1),
        "est_tokens": int(sum(_num(e.get("est_tokens")) for e in led) + _num(arc.get("est_tokens"))),
        "saved_tokens": int(sum(_num(e.get("saved_tokens")) for e in led) + _num(arc.get("saved_tokens"))),
    }
    price = _num((costs.get("price") or {}).get("usd_per_mtok"))
    out["usd_per_mtok"] = price
    out["est_usd"] = round(out["est_tokens"] * price / 1e6, 2) if price else None
    out["saved_usd"] = round(out["saved_tokens"] * price / 1e6, 2) if price else None
    n = max(1, out["sessions"])
    out["avg_tokens_per_build"] = int(round(out["est_tokens"] / n, -2))
    out["avg_usd_per_build"] = round(out["avg_tokens_per_build"] * price / 1e6, 3) if price else None
    return out


def week(budget_path, now=None):
    """Weekly Grok Bot limit numbers from tools/pace.py; None when budget.json is absent (public builds, CI)."""
    if not os.path.exists(budget_path):
        return None
    try:
        import json
        import pace
        with open(budget_path, encoding="utf-8") as f:
            b = json.load(f)
        if now is None:
            try:
                from zoneinfo import ZoneInfo
                now = dt.datetime.now(ZoneInfo(b.get("timezone", "America/Denver"))).replace(tzinfo=None)
            except Exception:
                now = dt.datetime.now()
        r = pace.compute(b, now)
    except Exception:
        return None
    keep = ("now", "reset", "reading_at", "reading_pct", "est_used_pct", "target_pct", "pace_line_pct",
            "hours_left", "sessions_left", "per_session_pct", "recommend")
    return {k: r[k] for k in keep}   # numbers and times only: never task text


def summarize(costs, budget_path, cap_saved_bytes=0, now=None):
    led = [e for e in costs.get("ledger", []) if isinstance(e, dict)]
    sav = [s for s in costs.get("savings", []) if isinstance(s, dict)]
    top = sorted(sav, key=lambda s: -_num(s.get("tokens_saved")))
    return {
        "lifetime": lifetime(costs),
        "price": costs.get("price") or {},
        "method": costs.get("method", ""),
        "saved_method": costs.get("saved_method", ""),
        "trend": [{"session": e.get("session", ""), "est_tokens": int(_num(e.get("est_tokens"))),
                   "saved_tokens": int(_num(e.get("saved_tokens")))} for e in led][-LEDGER_IN_DATA:],
        "biggest": [{k: s.get(k) for k in ("change", "tokens_saved", "status", "link", "est_saving") if s.get(k) is not None}
                    for s in top[:3]],
        "cap_saved_kb_now": round(cap_saved_bytes / 1024, 1),
        "week": week(budget_path, now),
    }
