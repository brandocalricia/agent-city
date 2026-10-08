# Agent City suggestions for Grok Build

Generated 2026-10-08 18:33 UTC by build_data.py; refreshed every city session. Read by the `city-apply` skill.
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

- 2026-10-08 Quick YES 8/10: Should the Prompt Workshop get a linter that checks a pasted prompt for goal, context, done-when, and output, and offers the missing lines to copy? Reason: The four parts match the Delegate template agents already respond best to; checking runs in the browser, so it is instant and free. Red Team: keyword checks can miss a well-written prompt; accepted, it only suggests and never blocks.
- 2026-10-08 Quick YES 9/10: Should large publishes be pushed to a `publish` branch in pieces and then moved to main in one commit by a GitHub Action (tests first, refusing to overwrite newer work), instead of a chain of direct pushes to main? Reason: Pushes to a branch never touch the live site, so a publish that stops partway leaves nothing half-live, which is what stranded the last two publishes. Opening pull requests from a scheduled run needs the owner to confirm a form, so an Action does the one-step move. Red Team: an Action that writes to main could overwrite newer work; rebutted, it refuses whenever main changed in files the branch differs on, and it never force-pushes.
- 2026-10-08 Quick YES 9/10: Should every new Tutor problem include a short `answer` (a final expression in x when possible) and an optional `accept` list, so the Study Hall can check typed answers in the browser before the solution unlocks? Reason: Pragmatist: trying before peeking is how the problems actually help with Calc I quizzes. Resource Realist: one short field per problem, no extra calls. Risk Officer: the checker is a tiny parser with no eval, so typed text cannot run code. Red Team: the answer key is visible in data.js; rebutted, the full solution already is, and the lock is a study nudge, not security.
- 2026-10-08 Quick YES 8/10: Should the Morning Brief kiosk replace the front-right plaza planter, combining the Courier's and Timekeeper's notes on the local copy only, with a clean empty state on the public site? Reason: Pragmatist: one place to read the day instead of two panels. Risk Officer: it reads only private.js, which the public site never loads, and a static test guards that. User Voice: the counts on the sign tell him at a glance whether to open it. Red Team: public visitors see a box that says 'local copy only'; accepted, that is the empty state the rules require, and it links to both roles.
- 2026-10-08 Quick YES 8/10: Should this session push the rest of the UI overhaul (stuck on the ui-overhaul branch, CI green) to main in the same single commit as tonight's work? Reason: Pragmatist: the public city lags its own changelog, which looks broken. Risk Officer: the files match a branch that passed CI on ubuntu and macOS and render with no errors here; one revert undoes it. Resource Realist: one bigger push now beats re-explaining the mismatch every session. Red Team: the branch might have been held on purpose; rebutted, the design already had a Council YES and nothing marks it as held.

## Next best steps for the city (context)

1. (U) Review Board checklist view: the Critic's pass/fail checks as icons per role
2. (W) Agents follow sidewalks/crosswalks; idle animations by role (reading, typing, hammering)
3. (U) Notice Board: dismiss/snooze notices locally (localStorage)
4. (W) Weather: rain/snow toggle (snow for Denver winters)
5. (U) Market: dim stale finds (>30 days) and tag finds by class/topic with filters

## Newsroom: recent news for Grok Build (context, not actionable)

- 2026-10-08 [Grok Build 1.0.46: session-start rules survive prompt rebuilds; grok inspect reports MCP sources](https://x.ai/build/changelog) (grok-build): The city's global rule and SessionStart hook load at session start; this fix keeps them in force in long sessions. Worth being on 1.0.46+ (grok update).
- 2026-10-08 [Grok Build 1.0.44 adds /context-window and per-model context choices](https://x.ai/build/changelog) (tokens): A smaller context window for routine sessions (city-apply, quick fixes) is a direct token saving; keep the big window for refactors.
- 2026-10-08 ["Time to rewrite" (TTR): measuring how agent-ready a codebase is](https://x.com/i/trending/2108003942076408271) (technique): Same idea as AGENTS.md: specs next to code and tests an agent can run. Supports keeping the city's AGENTS.md and tests current every session.

## Scout finds for Grok Build (context)

(none yet)
