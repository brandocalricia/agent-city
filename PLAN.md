# PLAN: Stabilize gb-free Model Diversity (b9div1)

## Goal
Fix gb-free lane ordering so traffic rotates across nemotron-super, nemotron-ultra, and Gemini Flash, keeping failover to the next free lane intact. One model must not exceed ~70% of successful requests.

---

## Current State (Measured from shim.log since 19:11:00)

| Model | Successful Requests | Share |
|-------|---------------------|-------|
| nvidia/nemotron-3-super-120b-a12b | 41 | **80.4%** |
| openrouter/nvidia/nemotron-3-super-120b-a12b:free | 9 | 17.6% |
| nvidia/nemotron-3-ultra-550b-a55b | 1 | 2.0% |
| gemini/gemini-3.8-flash | 0 (errors/cooldown) | 0% |
| gemini/gemini-3.7-flash | 0 (errors/cooldown) | 0% |
| **Total** | **51** | 100% |

**Problem**: nemotron-super handles >80% of traffic because it's first in the lane order and rarely cools down. The cooldown mechanism only kicks in after failures.

---

## Root Cause
In `~/.local/bin/omniroute-nullstrip.py`, the `order(lanes)` function returns all non-cooling lanes in their original order, then cooling lanes. Since nemotron-super (first in `gb-free` list) almost never fails, it never cools down and gets most traffic while it's healthy.

---

## Fix: Round-Robin Among Healthy Lanes
Modify `order(lanes)` to rotate the first healthy lane to the end after each successful request, so traffic distributes across all available models.

**Proposed changes to `~/.local/bin/omniroute-nullstrip.py`:**
1. Add `_rr_index = {}` dict to track round-robin position per model alias (top-level)
2. In `order(lanes, alias=None)`: 
   - Accept optional `alias` parameter
   - When `alias` provided and hot lanes exist, rotate hot list by `_rr_index[alias] % len(hot)`
3. In `_attempt()`: On success, increment `_rr_index[alias]` (only for successful deliveries)

This ensures:
- Traffic distributes across healthy lanes in round-robin fashion
- Failed lanes still cool down and are skipped
- On failure, we try next lane in rotated order (failover intact)
- Only successes advance the round-robin index

---

## Files to Change
- `~/.local/bin/omniroute-nullstrip.py` — modify `order(lanes)` and add round-robin state

---

## Acceptance Criteria
- **Before fix**: nemotron-super ~80% of gb-free requests (measured)
- **After fix**: No single model >70% across 20 test requests spread across ≥2 models
- Failover still works (cooldown lanes skipped, retries on next healthy lane)
- Existing tests exit 0 (`python3 -m unittest discover -s tests` in agent-city-w2)
- No restarts that kill other workers' sessions
- Free OmniRoute only, no SuperGrok

---

## Implementation Notes (for Grok Bot)
- Backup: `cp omniroute-nullstrip.py omniroute-nullstrip.py.bak-b9div1`
- Verify syntax: `python3 -m py_compile omniroute-nullstrip.py`
- Check ultra is in hot list (not missing/marked cold)
- Confirm `_attempt()` moves to next lane on failure (only success advances `_rr_index`)
- Restart shim: `systemctl --user restart omniroute-nullstrip.service` (when safe)
- Verify: 20 requests on ≥2 models, ultra included if healthy, forced-failure shows fallthrough