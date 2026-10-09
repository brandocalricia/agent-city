# Agent City suggestions for Grok Build

Generated 2026-10-09 13:26 UTC by build_data.py; refreshed every city session. Read by the `city-apply` skill.
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

- 2026-10-09 Quick YES 8/10: Should every [publish] run tools/privacy_check.py before Tests and stop the publish on any email or amount hit? Reason: One-line step, the repo already scans clean, and a leak to the public site cannot be undone; a false positive only delays a publish and is fixed with the allowlist
- 2026-10-08 Quick YES 7/10: Catch up the missed 8:49 AM roles at midday (Courier, Timekeeper, Tutor), skipping Scout deep research and the Newsroom since today's digest exists? Reason: Keeps the Morning Brief and Study Hall fresh after a failed session while staying inside this session's M budget
- 2026-10-08 Quick YES 9/10: Skip the test workflow on partial publish-branch pushes, but still run it on the final [publish] commit? Reason: Partial pushes are incomplete by design, so their failures were pure noise (about 15 emails); the [publish] commit still gets the full ubuntu + macOS run and publish.yml still gates main
- 2026-10-08 Quick YES 8/10: Fade overlapping building labels, keeping Town Hall's label always visible? Reason: Overlapping names were unreadable in the overview; one small throttled file fixes it and is easy to undo; search and the minimap still reach every building
- 2026-10-08 Quick YES 8/10: Should the Prompt Workshop get a linter that checks a pasted prompt for goal, context, done-when, and output, and offers the missing lines to copy? Reason: The four parts match the Delegate template agents already respond best to; checking runs in the browser, so it is instant and free. Red Team: keyword checks can miss a well-written prompt; accepted, it only suggests and never blocks.

## Next best steps for the city (context)

1. (U) privacy_check `--files` mode + line numbers: scan only the files a publish changes and print `path:line` so a hit is fixed in seconds (feeds R-006)
2. (U) Reviewed allowlist file for privacy_check (`tools/privacy_allow.txt`, one pattern + reason per line, Council YES to add) so a false positive never tempts anyone to turn the gate off
3. (U) Session heartbeat JSON (local): last start/finish/ok written each session; Notice Board surfaces a missing heartbeat (feeds R-008)
4. (U) Review Board checklist view: the Critic's pass/fail checks as icons per role
5. (W) Agents follow sidewalks/crosswalks; idle animations by role (reading, typing, hammering)

## Newsroom: recent news for Grok Build (context, not actionable)

- 2026-10-09 [Grok Build 1.0.50: worktree rm refuses dirty or in-use worktrees without -f](https://x.ai/build/changelog) (grok-build): A remove that stops when a worktree is dirty or in use keeps the city from deleting the owner's work by mistake.
- 2026-10-08 [Grok Build 1.0.46: session-start rules survive prompt rebuilds; grok inspect reports MCP sources](https://x.ai/build/changelog) (grok-build): The city's global rule and SessionStart hook load at session start; this fix keeps them in force in long sessions. Worth being on 1.0.46+ (grok update).
- 2026-10-08 [Grok Build 1.0.44 adds /context-window and per-model context choices](https://x.ai/build/changelog) (tokens): A smaller context window for routine sessions (city-apply, quick fixes) is a direct token saving; keep the big window for refactors.
- 2026-10-08 ["Time to rewrite" (TTR): measuring how agent-ready a codebase is](https://x.com/i/trending/2108003942076408271) (technique): Same idea as AGENTS.md: specs next to code and tests an agent can run. Supports keeping the city's AGENTS.md and tests current every session.

## Scout finds for Grok Build (context)

(none yet)
