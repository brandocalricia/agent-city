# PLAN: OmniRoute Analytics Accuracy (b9anlyt1)

## Goal
Every stat on the OmniRoute Home and Analytics pages must match ground truth from the OmniRoute SQLite DB (read-only) and shim.log. No silent drifts. Est. cost is out of scope — w3 owns b9estcost1.

---

## OmniRoute Home / Analytics Page Stats (to list in PLAN.md)

### 1. Total Requests
- **Source**: `SELECT COUNT(*) FROM usage_history` (SQLite DB) vs shim.log line count (gb-free: 336 requests counted since 19:11)
- **Dashboard value**: [to be measured after UI loads]
- **DB value**: [COUNT from usage_history table]
- **Computed value**: [shim.log OK line count]
- **Match**: Yes/No

### 2. Per-Model Success Count
- **Source**: `SELECT model, COUNT(*) FROM usage_history WHERE success='1' GROUP BY model` (SQLite DB) vs per-model count from shim.log OK lines
- **Dashboard value**: [to be measured]
- **DB value**: [model breakdown from DB]
- **Computed value**: [from shim.log — e.g. super 197, ultra 19, laguna 42, lightning 59 of 336 total]
- **Match**: Yes/No

### 3. Per-Provider Success Count
- **Source**: `SELECT provider, COUNT(*) FROM usage_history WHERE success='1' GROUP BY provider` (SQLite DB)
- **Dashboard value**: [to be measured]
- **DB value**: [provider breakdown from DB]
- **Computed value**: [from shim.log — NVIDIA vs OpenRouter vs Gemini counts]
- **Match**: Yes/No

### 4. Average Latency
- **Source**: `SELECT AVG(latency_ms) FROM usage_history WHERE success='1'` (SQLite DB) vs average from shim.log timestamps
- **Dashboard value**: [to be measured]
- **DB value**: [AVG latency from DB]
- **Computed value**: [from shim.log — e.g. 9.33s avg for gb-free OK lines]
- **Match**: Yes/No

### 5. Lane Health (not cooled)
- **Source**: `SELECT lane, _cool FROM lane_cooldown` (SQLite DB, _cool timestamp) vs lanes where `_cool <= now` in shim
- **Dashboard value**: [to be measured — which lanes are "healthy"]
- **DB value**: [from DB cooldown table — currently none in usage_history context]
- **Computed value**: [from shim.log — _cool.get(lane, 0) <= now check]
- **Match**: Yes/No

### 6. Round-Robin Index per Alias
- **Source**: `_rr_index` dict in omniroute-nullstrip.py (code) vs any UI display
- **Dashboard value**: [to be measured]
- **DB value**: [N/A — in-memory state]
- **Computed value**: [from shim — _rr_index[alias] values]
- **Match**: N/A (internal state)

### 7. Cooldown Timestamps
- **Source**: `SELECT lane, _cool FROM lane_cooldown` (SQLite DB)
- **Dashboard value**: [to be measured]
- **DB value**: [exact timestamps from DB]
- **Computed value**: [from shim.log — cool timestamps]
- **Match**: Yes/No

### 8. Stream First-Content Timeout
- **Source**: `SHIM_FIRST_CONTENT_S` env var (100s default) vs dashboard display
- **Dashboard value**: [to be measured]
- **DB value**: [100 from config]
- **Computed value**: [from shim source code]
- **Match**: Yes/No

---

## Verification Steps

### Step 1: Count Stats from shim.log (Read-Only)
Run the following commands to compute values from the live shim log:

```bash
# Total successful gb-free requests
grep " gb-free OK " ~/.omniroute/logs/shim.log | wc -l

# Per-model counts (column 5 = model name)
grep "gb-free.*OK" ~/.omniroute/logs/shim.log | awk '{print $5}' | sort | uniq -c | sort -rn

# Per-model latency measurements (column 6 = latency)
grep " gb-free OK " ~/.omniroute/logs/shim.log | awk '{print $6}' | head -20

# Round-robin index values (from code inspection)
grep "_rr_index" /home/brandonrobertniehaus/.local/bin/omniroute-nullstrip.py
```

### Step 2: Query the SQLite DB for Ground Truth
```bash
python3 -c "
import sqlite3
conn = sqlite3.connect('/home/brandonrobertniehaus/.omniroute/storage.sqlite')
cursor = conn.cursor()
cursor.execute('SELECT COUNT(*) FROM usage_history')
print('DB total:', cursor.fetchone()[0])
cursor.execute(\"SELECT model, COUNT(*) FROM usage_history WHERE success='1' GROUP BY model ORDER BY COUNT(*) DESC\")
for row in cursor.fetchall():
    print(f'  Model: {row[0]}, count: {row[1]}')
cursor.execute(\"SELECT provider, COUNT(*) FROM usage_history WHERE success='1' GROUP BY provider ORDER BY COUNT(*) DESC\")
for row in cursor.fetchall():
    print(f'  Provider: {row[0]}, count: {row[1]}')
cursor.execute('SELECT AVG(latency_ms) FROM usage_history WHERE success='1')
print('Avg latency (ms):', cursor.fetchone()[0])
conn.close()
"
```

### Step 3: Build Dashboard vs Log Mismatch Table
Create a table comparing:
| Stat | Dashboard Value | DB Value | Computed (shim.log) | Match? |
|------|----------------|----------|---------------------|--------|
| Total requests | | | 336 | |
| Lightning success count | | | 59 | |
| Super success count | | | 197 | |
| Laguna success count | | | 42 | |
| Average latency | | | 9.33s | |
| Cooldown active lanes | | | [count] | |

### Step 4: Fix Mismatches at Source
- If DB count ≠ shim.log count, check: is the DB being written to by another process? Is there a race condition?
- If per-model counts don't match, check: are some models being double-counted? Is the cooldown logic correct?
- All fixes are read-only on the OmniRoute config — propose changes on Channel; Grok Bot applies.

### Step 5: Add Check Script
Create `tests/analytics_truth.py` that:
- Reads from SQLite DB (`/home/brandonrobertniehaus/.omniroute/storage.sqlite`)
- Reads from shim.log (`~/.omniroute/logs/shim.log`)
- Computes the same stats the dashboard shows
- Exits non-zero on any mismatch (exit code 1 if any stat differs by more than a negligible threshold)
- Can be rerun: `python3 -m unittest discover -s tests`

### Step 6: Post PROGRESS
Post a table of stat/UI/DB before+after values. Include the check script exit code.

### Step 7: DONE
Post DONE --re b9anlyt1 with files changed and sha.

---

## Acceptance Criteria
- PLAN.md lists all 8+ stats with source queries, UI values, DB values, and computed values
- Mismatch table completed with Yes/No for each stat
- Check script `tests/analytics_truth.py` exits 0 when values match, exits non-zero when they don't
- Existing tests (`python3 -m unittest discover -s tests`) exit 0
- No city / Agent Office / b9cityavo1 files touched (stay on free OmniRoute lane)
- Shim NOT edited (frozen per PR #2 review)
- Stats sourced from SQLite DB (read-only) and shim.log (read-only)

---

## Files Changed (to commit on w2/b9anlyt1)
- `PLAN.md` — this complete plan with stat list, mismatch table, and check script specs
- `tests/analytics_truth.py` — new check script (created)
- Any other files needed for the analytics verification

---
## Key Notes
- **b9div1** is ACCEPTED+CLOSED — round-robin fix live, shim NOT edited
- **OmniRoute shim** is frozen — no edits allowed
- **City files** left alone (b9cityavo1 stays HOLD)
- **Cost analysis** out of scope (w3 owns b9estcost1)
- Stats must be verified against SQLite DB and shim.log only
- Fix proposals go on Channel; Grok Bot applies