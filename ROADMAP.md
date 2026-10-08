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
- [x] 29. Mobile/touch: tap to open, bottom-sheet panels, saver graphics on phones (virtual joystick moved to #46)

## Backlog (top = next)
5. [ ] (U) Review Board checklist view: the Critic's pass/fail checks as icons per role
6. [ ] (W) Agents follow sidewalks/crosswalks; idle animations by role (reading, typing, hammering)
7. [ ] (U) Notice Board: dismiss/snooze notices locally (localStorage)
8. [ ] (W) Weather: rain/snow toggle (snow for Denver winters)
10. [ ] (U) Market: dim stale finds (>30 days) and tag finds by class/topic with filters
11. [ ] (W) Sounds toggle: ambient city + fountain + click blips (WebAudio, off by default)
12. [ ] (W) Cars with headlights on the roads (instanced, cheap)
13. [ ] (U) Stats Tower: 7-day sparkline of actions per day
15. [ ] (U) Archive timeline: browse weekly summaries and CHANGELOG entries
16. [ ] (W) Real sunrise/sunset from a solar formula for Denver + moon phase at night
17. [ ] (U) Candidate role: Sentinel (account-security watch: password resets, new-device sign-ins, new app authorizations; local only)
18. [ ] (W) Sports field district on the city edge (practice times from calendar, local only)
19. [ ] (W) Campus district with class-location markers (local only)
20. [ ] (U) Tutor streak tracker (problems attempted, localStorage)
21. [ ] (U) Prompt Workshop: save favorite templates (localStorage)
22. [ ] (W) Skill Forge glows brighter while a Librarian proposal is waiting
23. [ ] (W) Minimap pulses roles that acted today
24. [ ] (U) Office: per-session build timeline with screenshots
25. [ ] (W) Toolsmith workbench animation once a find is approved
26. [ ] (U) "Copy prompt" buttons on more panels (role-specific asks for Grok Bot)
27. [ ] (W) Seasonal decorations (snow caps in winter, school-color flags on game days)
28. [ ] (W) Photo mode: hide UI, slow cinematic orbit, save PNG
30. [ ] (U) Performance pass: label culling, LOD for far buildings, FPS counter in saver mode
31. [ ] (W) Drone tour: one-click guided tour of all landmarks with captions
32. [ ] (W) Light ambient pedestrians for atmosphere only (purely visual, cheap)
35. [ ] (U) Council docket: open roadmap items and Notice Board items waiting for a verdict, shown in Town Hall
36. [ ] (W) Town Hall's beacon glows green or red for a few seconds after a fresh YES or NO verdict
37. [ ] (U) Grok Build Pier: a harbor building on the city edge for the Grok Build feed (queue, ids, which roles sent them); later, applied/declined counts if the owner opts into publishing a summary
38. [ ] (U) Prompt linter as a Grok Build skill (/prompt-lint): checks a prompt for goal, context, done-when, and output before work starts; shared rules with roadmap #4
39. [ ] (U) Archive rotation: move activity.json lines and CHANGELOG entries older than 30 days into archive/ files so every session reads and pushes less
40. [ ] (U) Grok Build cost log: the helper appends tokens/time per applied item to a local file; the owner can opt in to sharing totals with the Meter Reader
41. [ ] (U) Message-link panel: a Post Office window showing the link's health (last message each way, watcher seen, sends this hour) without message contents
42. [ ] (U) Newsroom follow-ups: the Reporter marks a story 'confirmed' or 'retracted' when a primary source appears, and the Scout opens a find for confirmed tools
43. [ ] (U) "Copy link" button in every panel header (copies the deep link, so a panel can be sent to Grok Bot or Grok Build)
44. [ ] (W) Deep-link tours: #tour=morning flies through the buildings that changed today, one caption each
45. [ ] (W) Streak replay: a dashboard timeline that replays today's neon streaks in order, with the action under each
46. [ ] (U) Phone walk mode: virtual joystick + drag to look
47. [ ] (U) Treasury: cost per role, once the Meter Reader tags pushed files by the role that changed them
48. [ ] (U) Study Hall practice set: the last 5 Tutor problems, each with its own answer box; results kept in localStorage (feeds the streak tracker, #20)
49. [ ] (U) Answer checker for Econ: numbers with units and a tolerance (e.g. elasticity -1.2, price $14), and CS outputs compared line by line
50. [ ] (W) Morning Brief kiosk sign glows warm from 6 to 10 AM Denver time and dims after the brief is opened
51. [ ] (U) Morning Brief: free study blocks from the Timekeeper become one-click 'study Calc I at 12:00' prompts (local only)
52. [ ] (U) Inspector live-version check: compare the live site's City.version with the last published one at the start of every session and finish any stalled publish first
53. [ ] (U) HUD polish: the top-left status chips overlap each other at some widths; wrap or merge them
54. [ ] (U) Prompt linter 'Fix it for me': a copy button that asks Grok Bot to rewrite the prompt with the missing parts filled from context
55. [ ] (U) Label priority by activity: buildings whose role acted today win label overlaps and get a small dot (pairs with #23)
56. [ ] (U) Missed-session recovery: when a scheduled session fails, the next one reads a small local state file and runs the roles it missed (as done by hand at midday Oct 8)
57. [ ] (U) Morning Brief bills card (local only): dues and bills from the Courier with a 'pay or check by' countdown, never public
