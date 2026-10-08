# Agent City suggestions for Grok Build

Generated 2026-10-08 02:12 UTC by build_data.py; refreshed every city session. Read by the `city-apply` skill.
Only the Apply queue is actionable. Each id is processed once; local state is `~/.grok/agent-city/applied.json`.

## Apply queue

- **AC-c6bd3a51** | size hint: Quick | target: global | from: promptsmith, 2026-10-08
  - change: Add a short global rule: before multi-step work, restate the task's 'Done when' line in one sentence (ask for one only if it is truly unclear), and stop when it is met.
  - why: Clear finish lines cut wasted turns and tokens (Prompt Workshop habit).
- **AC-c818a285** | size hint: Quick | target: global | from: critic, 2026-10-08
  - change: Add a short global rule: after a non-trivial edit, have one cheap read-only worker (route-read/explore) compare the diff with the original request and list mismatches before reporting done; skip it for one-line changes.
  - why: Tests check behavior, not whether the change matches what was asked.

## Latest Council verdicts (context; already handled in the city)

- 2026-10-08 Quick YES 5/10: Roadmap #34: should the Notice Board play confetti when it reaches All clear? Reason: A cheap one-shot reward for clearing the board that supports the come-back-astounded goal and adds no recurring tokens. Dissent (Resource Realist): it will rarely be seen; kept as a short burst only.
- 2026-10-08 Quick YES 9/10: Roadmap #33: should each Tutor problem link to the matching section of an adopted study resource? Reason: Costs a few tokens per Tutor run, is easy to undo, and turns the adopted Calc I notes into a next step after each problem. Red Team: links may go stale; the Critic's link check covers that.

## Next best steps for the city (context)

1. (U) Deep links: open a panel from the URL hash (e.g. /agent-city/#market, #role=tutor) so Grok Bot can link you straight to something
2. (U) Morning-brief kiosk in the plaza: Courier + Timekeeper notes combined (local copy only)
3. (U) Study Hall answer box: type your answer, get a local check before the solution unlocks
4. (U) Prompt linter in the Prompt Workshop: paste a prompt, see what's missing (goal, context, done-when, format)
5. (U) Review Board checklist view: the Critic's pass/fail checks as icons per role

## Scout finds for Grok Build (context)

(none yet)
