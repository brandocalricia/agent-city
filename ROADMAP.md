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
62. [ ] (U) pace.py `--check` mode run by tests and each session start: flags any budget entry with an unreadable time, missing tier/estimate, or a future date, naming the entry instead of giving up on the whole file (feeds R-008)
63. [ ] (U) Channel report-quality board in the Savings Hub: share of Grok Build DONE posts that carried evidence (SHA, URL, test output) vs bare claims, per lane, so a lane that writes junk is visible at a glance
64. [ ] (U) Notice Board "paced down" line: when pace.py says minimal/skip, show one plain sentence with the points over pace so a quiet session never looks like a stall
65. [ ] (U) Channel thread digest in the Savings Hub: group each task's ACK, DONE and BLOCKED posts into one row with times, so retries and stale backoffs are obvious
66. [ ] (U) Stale publish-branch sweeper: the Inspector deletes a remote `publish` branch whose commits are already on main, so it never blocks the next publish
67. [ ] (U) Pending local log counter: show how many CHANGELOG/activity lines are waiting for the next publish, so batched minimal sessions stay visible
68. [x] (merged into #66, Oct 9) Publish preflight in pace/Inspector: before a session publishes, check for a remote `publish` branch and say in one line whether it is stale (already on main) or live (another session), so nobody force-overwrites or stalls
69. [ ] (U) Channel "waiting on" line on the Notice Board: the oldest Grok Bot task with no Grok Build ACK and how long it has waited, shown calmly (Wi-Fi gaps are normal) so a nudge is a glance, not a hunt
70. [ ] (U) Courier sign-in digest: group new-login and new-app emails into one calm "confirm these were you" line instead of separate notices
71. [ ] (U) Pace banner in the Treasury: show points over/under pace and how many sessions were held, so a run of quiet sessions reads as deliberate saving
72. [ ] (U) Held-session counter in pace.py: after 4+ held sessions in a row, recommend one polish-sized publish of the batched logs so the live changelog doesn't fall a day behind
73. [ ] (U) Channel closed-task list: when Grok Bot verifies a DONE (an "ok" reply), mark that task closed in channel-seen.json so later sessions skip rereading its thread
74. [ ] (U) Cloudflare lane card in the Savings Hub: show a plain "needs Account ID" state when Workers AI returns 502 for a missing setting, so a setup gap never looks like an outage
75. [ ] (U) Probe-based "N of M up" on the public OmniRoute snapshot: count a lane as up only when a live probe passed in the last 15 minutes, matching the Grok Build status line
76. [ ] (U) Stale-data badge on Treasury and Router Hub: when the OmniRoute Usage Analytics snapshot is older than 15 minutes, show "last live reading at HH:MM" in place of the savings figure, so a delayed number never looks current
77. [ ] (U) Channel DONE lint: flag grok-build DONE posts that carry no evidence (unfilled template text, "continuation note") so the reply rejects them on the first pass
78. [ ] (U) Owner-urgent lane in the Channel digest: show OWNER URGENT tasks pinned at the top with time since ACK, so an urgent provider fix is never buried under routine follow-ups
79. [ ] (U) Duplicate-DONE folding: when Grok Build posts the same DONE under two ids (e.g. gdb9err2 and gdb9err2b), the Channel digest shows one row with both ids, so dedup is visible and nothing is answered twice
80. [ ] (U) Hold-streak guard: when the Council has held the Builder for 4+ sessions in a row, the next session that the pacer rates S or better must ship one polish increment, so pacing never freezes the city all day
81. [x] (merged into the Watchman role, Oct 9) Branch CI note on the Notice Board: show red Actions runs on Grok Build PR branches separately from main, labeled "not live", so a failing PR branch never reads as a broken site
82. [ ] (U) Watchman card in Town Hall: last check time, main and live-site status, and each open PR's checks with a "not live" tag, read from the Watchman's own activity lines
83. [ ] (U) Channel reads by time: each session asks the Channel PR only for comments since the last-seen timestamp in channel-seen.json, so a long thread never gets reread in full
59. [ ] (U) Session heartbeat JSON (local): last start/finish/ok written each session; Notice Board surfaces a missing heartbeat (feeds R-008)
5. [ ] (U) Review Board checklist view: the Critic's pass/fail checks as icons per role
6. [ ] (W) Agents follow sidewalks/crosswalks; idle animations by role (reading, typing, hammering)
7. [ ] (U) Notice Board: dismiss/snooze notices l