# Agent City suggestions for Grok Build

Generated 2026-10-10 23:23 UTC by build_data.py; refreshed every city session. Read by the `city-apply` skill.
Only the Apply queue is actionable. Each id is processed once; local state is `~/.grok/agent-city/applied.json`.
Every item carries checks (run before and after; `$ ` lines are commands) and tests (must pass). Items without them are skipped.

## Apply queue

- **AC-c6bd3a51** | size hint: Quick | target: global | from: promptsmith, 2026-10-08
  - change: Add a short global rule: before multi-step work, restate the task's 'Done when' line in one sentence (ask for one only if it is truly unclear), and stop when it is met.
  - why: Clear finish lines cut wasted turns and tokens (Prompt Workshop habit).
  - check: $ grok inspect >/dev/null 2>&1
  - check: No rule in ~/.grok/rules or ~/.grok/AGENTS.md already tells Grok to state a 'Done when' line (no duplicate guidance)
  - test: $ grep -q '^## {id}' {rules_file}
  - test: $ grok inspect 2>&1 | grep -q 45-agent-city-applied
- **AC-c818a285** | size hint: Quick | target: global | from: critic, 2026-10-08
  - change: Add a short global rule: after a non-trivial edit, have one cheap read-only worker (route-read/explore) compare the diff with the original request and list mismatches before reporting done; skip it for one-line changes.
  - why: Tests check behavior, not whether the change matches what was asked.
  - check: $ grok inspect >/dev/null 2>&1
  - check: route-read or explore exists as a sub-agent type (grok inspect lists it), and no rule already requires a diff-vs-request review
  - test: $ grep -q '^## {id}' {rules_file}
  - test: $ grok inspect 2>&1 | grep -q 45-agent-city-applied
- **AC-c4ffa8f0** | size hint: Quick | target: global | from: optimizer, 2026-10-08
  - change: Add a short global rule: for files over about 400 lines, search first (rg or grep) and read only the needed line ranges instead of the whole file; re-read a file only if it changed since the last read.
  - why: Whole-file reads of big files are the largest avoidable context cost in a coding session (Optimizer).
  - check: $ grok inspect >/dev/null 2>&1
  - check: No rule in ~/.grok/rules or ~/.grok/AGENTS.md already gives a read-by-range instruction (no duplicate guidance)
  - test: $ grep -q '^## {id}' {rules_file}
  - test: $ grok inspect 2>&1 | grep -q 45-agent-city-applied

## Latest Council verdicts (context; already handled in the city)

- 2026-10-09  YES ?/10:  Reason: 
- 2026-10-09  YES ?/10:  Reason: 
- 2026-10-09 Quick NO build (minimal session) 9/10: Build this session while usage runs about 18 points ahead of pace? Reason: No breakage and no open owner requests; spending now risks the weekly limit
- 2026-10-09 Quick NO build (minimal session) 9/10: Build this session while usage runs about 19 points ahead of pace? Reason: No breakage and no open owner requests; spending now risks the weekly limit
- 2026-10-09 Quick NO build (minimal session) 9/10: Build this session while usage runs about 20 points ahead of pace? Reason: Spending now would risk the weekly limit before reset; no open owner requests or breakage

## Next best steps for the city (context)

1. (U) privacy_check `--files` mode + line numbers: scan only the files a publish changes and print `path:line` so a hit is fixed in seconds (feeds R-006)
2. (U) Reviewed allowlist file for privacy_check (`tools/privacy_allow.txt`, one pattern + reason per line, Council YES to add) so a false positive never tempts anyone to turn the gate off
3. (U) pace.py `--check` mode run by tests and each session start: flags any budget entry with an unreadable time, missing tier/estimate, or a future date, naming the entry instead of giving up on the whole file (feeds R-008)
4. (U) Channel report-quality board in the Savings Hub: share of Grok Build DONE posts that carried evidence (SHA, URL, test output) vs bare claims, per lane, so a lane that writes junk is visible at a glance
5. (U) Notice Board "paced down" line: when pace.py says minimal/skip, show one plain sentence with the points over pace so a quiet session never looks like a stall

## Newsroom: recent news for Grok Build (context, not actionable)

- 2026-10-10 [Leaked XPass tiers would bundle X Premium, SuperGrok, Cursor and Grok Bot in one shared usage pool](https://x.com/i/trending/2108385763071000885) (tokens): Summary: if real, Grok Build and Grok Bot quotas could merge, which would change how the Treasury paces both pools. Watch for an official announcement before acting.
- 2026-10-10 [Release workflow run end to end by coordinated Grok Bots in Slack](https://x.com/i/trending/2107586232075403441) (agents): Summary: a release bot delegating builds, fuzz swarms and fixes to an engineer bot mirrors the city's Grok Bot to Grok Build Channel handoff, with humans approving only the final step.
- 2026-10-10 [Grok 4.7 tops VulcanBench coding and the Artificial Analysis Cyber Index](https://x.com/i/trending/2106666031037223269) (model): Summary: Grok 4.7 stays the strongest main lane for hard Grok Build tasks, so free OmniRoute lanes should take routine work and Main Grok only the hard turns.
- 2026-10-09 [Grok Build 1.0.50: worktree rm refuses dirty or in-use worktrees without -f](https://x.ai/build/changelog) (grok-build): A remove that stops when a worktree is dirty or in use keeps the city from deleting the owner's work by mistake.
- 2026-10-08 [Grok Build 1.0.46: session-start rules survive prompt rebuilds; grok inspect reports MCP sources](https://x.ai/build/changelog) (grok-build): The city's global rule and SessionStart hook load at session start; this fix keeps them in force in long sessions. Worth being on 1.0.46+ (grok update).

## Scout finds for Grok Build (context)

(none yet)
