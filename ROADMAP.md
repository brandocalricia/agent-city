# Agent City - Roadmap

Prioritized backlog. Each item = one short session. Take the top unchecked item unless the user asks for something else.
Every Builder session adds at least 2 new ideas so the backlog stays 20+.
Legend: [x] done · [ ] todo · (W) wow factor · (U) useful

## Done
- [x] Day 1 (2026-10-08): streets, skyline, dusk sky, Library, Office, Town Hall, Market, walking assistant, orbit + walk, panels, build_data.py
- [x] Auditor: split index.html into small plain-script files (css/, js/, js/buildings/)
- [x] 0. USER REQUEST: role agents with buildings, speech bubbles, history, activity.json, private.json (local only)
- [x] 1. Library: one clickable book per real skill
- [x] 2. Office routines board + work board
- [x] 3. Day/night cycle synced to Denver time (T to preview)
- [x] 4. Prompt Workshop templates
- [x] 5. Skill Forge guide
- [x] 6. Market freshness: freshest first + "new" badges (stale dimming still todo, see below)
- [x] 7. Minimap with click-to-fly
- [x] 8. Notice Board in the plaza
- [x] 9. Stats Tower
- [x] USER REQUEST: Notice Board current; Toolsmith adopted 2 finds into the Study Hall
- [x] USER REQUEST: Council role + Council Chamber; first verdicts
- [x] 33. (Council YES 9/10) Tutor problems link to the matching study resource
- [x] 34. (Council YES 5/10) Notice Board confetti on All clear
- [x] USER REQUEST: Grok Build link (grok-build/: city-council, city-apply, prompts, suggestions feed, installer + SessionStart hook)
- [x] 14. Treasury cost chart: Meter Reader's ledger bars + Optimizer savings (USER REQUEST: cost agents + bulletproof Grok Build link, tests + CI)
- [x] USER REQUEST: Message link Grok Bot <-> Grok Build (private issue thread, watcher + send + bot-link skill, 28 tests)
- [x] 1. Deep links: #market, #role=tutor open a panel; the address bar follows the open panel (Council: use them in notes)
- [x] USER REQUEST: Newsroom + Reporter (morning news digest, news.json with 14-day expiry, routed to Council/Scout/Prompt Smith/Tutor/GB)
- [x] USER REQUEST: Treasury in plain language (lifetime tokens and money saved, cost per build, weekly limit vs plan, trend, biggest savings; lifetime totals persist in costs.json)
- [x] USER REQUEST: UI overhaul (design system, top bar, search, dashboard, tabs, settings, shortcuts, loading, welcome card, phone layout), visual upgrade, neon streaks to Town Hall
- [x] USER REQUEST: Town Hall (Council) at the center of the city: City Hall + Council Chamber merged into the hub; #council and #cityhall redirect
- [x] 9. Search box: type a building or role, fly there and open it (/ or Ctrl+K)
- [x] 2. Morning Brief kiosk in the plaza: Courier + Timekeeper notes combined (local copy only; public empty state)
- [x] 3. Study Hall answer box: local check (numeric for expressions in x) before the solution unlocks
- [x] 4. Prompt linter in the Prompt Workshop: paste a prompt, see what's missing (goal, context, done-when, output)
- [x] 53. (part) Label declutter: overlapping building names fade, the farther one first; Town Hall always stays (chips overlap still open, #53)
- [x] 58. (Council YES 8/10) privacy_check.py runs in publish.yml before Tests; every [publish] fails closed on email/amount hits (R-006 continues)
- [x] 29. Mobile/touch: tap to open, bottom-sheet panels, saver graphics on phones (virtual joystick moved to #46)

## Backlog (top = next)
<!-- Re-ranked 2026-10-08 evening Daily Council: safety + usefulness before Metropolis wow -->
R-006. [ ] (U) Security lethal-trifecta hardening: pre-publish privacy_check (in CI since 2026-10-09), gitleaks-style CI, pin Actions SHAs, email/news never become gb verbatim, keep requests.json local
R-002. [ ] (U) Useful Index: one-tap rate of city outputs + per-role useful/produced in Treasury; Council weights backlog by it
R-005. [ ] (U) Output evals with deterministic graders (20-50 cases; Tutor sympy; URL resolve; schema; show pass rate on Review Board)
R-008. [ ] (U) Token-free reliability: scheduled GA live-site smoke + session heartbeat on Notice Board + private backup of local state
R-011. [ ] (U) Test Engineer role: no test, no publish; coverage review each session; heavy tests on GB free lanes
R-012. [ ] (U) Maintainer role: rotate feature upkeep/obsolescence reviews; propose removals to Council
R-001. [ ] (W/U) Metropolis districts (Builder's Lab, Campus, Launchpad, Personal OS) + IDEALS rewrite; phased
R-003. [ ] (U) Durable Playbook/wiki per district (append-and-refine; privacy-careful)
R-004. [ ] (U) Launchpad career pipeline (deadline tracker, bullet bank, portfolio case study); owner submits himself
R-007. [ ] (U) Merge Study Hall with Q1 DU Tutor + spaced retrieval (shared weekly limit careful)
R-009. [ ] (U) Today view: phone-first digest outside the 3D scene
R-013..016. [ ] (W) Schedule I-like living city / skate / currency — after R-006, R-002, R-005, R-011; original art only
60. [ ] (U) privacy_check `--files` mode + line numbers: scan only the files a publish changes and print `path:line` so a hit is fixed in seconds (feeds R-006)
61. [ ] (U) Reviewed allowlist file for privacy_check (`tools/privacy_allow.txt`, one pattern + reason per line, Council YES to add) so a false positive never tempts anyone to turn the gate off
59. [ ] (U) Session heartbeat JSON (local): last start/finish/ok written each session; Notice Board surfaces a missing heartbeat (feeds R-008)
5. [ ] (U) Review Board checklist view: the Critic's pass/fail checks as icons per role
6. [ ] (W) Agents follow sidewalks/crosswalks; idle animations by role (reading, typing, hammering)
7. [ ] (U) Notice Board: dismiss/snooze notices l