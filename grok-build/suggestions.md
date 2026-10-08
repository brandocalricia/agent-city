# Agent City suggestions for Grok Build

Generated 2026-10-08 05:55 UTC by build_data.py; refreshed every city session. Read by the `city-apply` skill.
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

- 2026-10-08 Full YES 7/10: Is the Agent City <-> Grok Build interchange (public feed, manifest updater, city_apply helper, council gate) safe, cheap, and reliable enough to run unattended on the owner's machine every session? Reason: Integrity, process-once, rollback and resource limits are tested (68 tests, ubuntu + macOS CI) and every change still needs a local council YES plus passing checks and tests. Dissent (Devil's Advocate): `grok inspect` output and hook-before-rules ordering are unverified on a real Grok Build install, so global items may fail and roll back until confirmed.
- 2026-10-08 Quick YES 5/10: Roadmap #34: should the Notice Board play confetti when it reaches All clear? Reason: A cheap one-shot reward for clearing the board that supports the come-back-astounded goal and adds no recurring tokens. Dissent (Resource Realist): it will rarely be seen; kept as a short burst only.
- 2026-10-08 Quick YES 9/10: Roadmap #33: should each Tutor problem link to the matching section of an adopted study resource? Reason: Costs a few tokens per Tutor run, is easy to undo, and turns the adopted Calc I notes into a next step after each problem. Red Team: links may go stale; the Critic's link check covers that.

## Next best steps for the city (context)

1. (U) Deep links: open a panel from the URL hash (e.g. /agent-city/#market, #role=tutor) so Grok Bot can link you straight to something
2. (U) Morning-brief kiosk in the plaza: Courier + Timekeeper notes combined (local copy only)
3. (U) Study Hall answer box: type your answer, get a local check before the solution unlocks
4. (U) Prompt linter in the Prompt Workshop: paste a prompt, see what's missing (goal, context, done-when, format)
5. (U) Review Board checklist view: the Critic's pass/fail checks as icons per role

## Newsroom: recent news for Grok Build (context, not actionable)

- 2026-10-08 [Grok Build 1.0.46: session-start rules survive prompt rebuilds; grok inspect reports MCP sources](https://x.ai/build/changelog) (grok-build): The city's global rule and SessionStart hook load at session start; this fix keeps them in force in long sessions. Worth being on 1.0.46+ (grok update).
- 2026-10-08 [Grok Build 1.0.44 adds /context-window and per-model context choices](https://x.ai/build/changelog) (tokens): A smaller context window for routine sessions (city-apply, quick fixes) is a direct token saving; keep the big window for refactors.
- 2026-10-08 ["Time to rewrite" (TTR): measuring how agent-ready a codebase is](https://x.com/i/trending/2108003942076408271) (technique): Same idea as AGENTS.md: specs next to code and tests an agent can run. Supports keeping the city's AGENTS.md and tests current every session.

## Scout finds for Grok Build (context)

(none yet)
