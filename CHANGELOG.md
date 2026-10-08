# Agent City - Changelog

## 2026-10-08 - Channel PR + thread-only link (no webhook required)
- Pacing counts ad-hoc from every Grok Bot (e.g. Q1 DU Tutor / Math Tutor `source: math-tutor`); `pace.py` prints sessions / Agent City ad-hoc / math-tutor / other (reading drift); evening session report includes that breakdown
- Message channel is now an open **pull request** titled Channel in `agent-city-comms` (not an issue), so Agent City's PR-comment listener wakes instantly; `comms.py` finds it by title or creates branch `channel` + `channel/README.md` + `gh pr create`
- Thread-only is the default: `comms.py setup` with no URL/key succeeds (gh auth, create Channel PR + hello, write `AGENT_CITY_WEBHOOK=off`); webhook stays optional
- Global rule auto-starts the watcher when `bot-webhook.env` exists and gh is signed in (not only when a webhook URL is present)
- Session skill: every session first reads the Channel PR for new grok-build messages (dedupe by id; `channel-seen.json` gitignored); every grok-bot reply MUST start with `[from:grok-bot]`
- Tests, README, AGENTS.md, bot-link skill, and rule updated; site version `2026-10-08q` (adds midday declutter.js)

## 2026-10-08 - Midday: readable labels + quieter CI
- Building names no longer pile on top of each other: when two labels overlap on screen, the farther one fades out, Town Hall's always stays, and a hovered or open building wins (checked 4 times a second, nothing per frame)
- The test workflow now skips partial pushes to the publish branch, which were failing by design and sending about 15 failure emails this morning; the final [publish] commit is still tested on ubuntu and macOS
- The 8:49 AM session failed, so its roles were caught up: Morning Brief inbox notes refreshed on the local copy, and a new Econ problem in the Study Hall (price elasticity, midpoint method) with an answer key
- Quick Council: 3 YES verdicts; 3 new roadmap ideas

## 2026-10-08 - Channel bootstrap + one publish path
- Message link is self-bootstrapping on Grok Build: `comms.py` setup/watch/send find the open issue titled Channel by title (create + first hello if missing); nothing hard-codes #1. Setup accepts URL+key as plain text in the prompt (also --clipboard / --url/--key), stores chmod 600, never echoes the key. Session start auto-launches the watcher once bot-webhook.env exists
- Grok Bot replies by finding the Channel issue by title (noted in AGENTS.md)
- Newsroom schedule explicit in the session skill and AGENTS.md: full Reporter at 8:49 AM (5-8 stories), light check at 8:49 PM (at most 2, or skip)
- One publish method only: always the `publish` branch + `[publish]` + GitHub Action (never push straight to main from a session); skill, AGENTS.md, and Action agree
- Tests updated for Channel resolution and plain-text setup paste

## 2026-10-08 - Early morning: live site catch-up + prompt linter
- Fixed: the live site was still on an older version because the last two publishes stopped partway; the UI overhaul, the Morning Brief kiosk, and the Study Hall answer box are now live
- Publishing now goes through a `publish` branch: files are pushed there in pieces, then a GitHub Action runs the tests and moves the live site to all of them in one commit, so a publish that stops partway can never leave the site half-updated (Quick Council YES 9/10)
- Prompt linter in the Prompt Workshop (#promptworkshop): paste a prompt and see which of the four parts agents rely on (goal, context, done when, output) are missing, then copy it with the missing lines added; it checks on your device only
- Quick Council: 2 YES verdicts; 3 new roadmap ideas

## 2026-10-08 - Overnight: morning brief + answer box
- Morning Brief kiosk on the plaza (opposite the Notice Board, #kiosk): today's calendar notes and inbox flags in one panel on your local copy, with a note-count sign, a "not refreshed yet today" hint, and a copy-ready "plan my day" prompt; the public site shows a clean empty state and private notes never leave private.js
- Study Hall answer box (#studyhall): type your answer and it is checked on your device (expressions in x are compared numerically, so equivalent forms count); the solution unlocks after your first try. Tutor problems now carry a short answer key
- Fixed: the live site was still on the pre-overhaul version because the last publish stopped partway; the full UI overhaul is now live
- Pacing: the fallback schedule now matches the real every-3-hours routine (8 sessions a day), with a test
- Quick Council: 3 YES verdicts (publish the overhaul, kiosk placement, answer keys); 4 new roadmap ideas

## 2026-10-08 - Treasury + UI overhaul
- Town Hall (Council) now stands at the center of the city as its hub: City Hall and the Council Chamber merged into one domed hall with a glowing beacon; the districts sit around it, and old links (#council, #cityhall) open #townhall
- Neon streaks: when a role finishes a task, a thin trail in its color arcs from its building to Town Hall (about 2 s, at most 4 at once, recent ones replay on load, new ones appear live; off under reduced motion; toggle in Settings)
- Treasury in plain language: lifetime tokens saved (~128k) and money saved (~$0.77 at the $6 per 1M token API list price, an estimate), cost per build, builds measured, this week's Grok Bot limit used vs plan, a savings trend, the biggest savings with links, and how every number is made; lifetime totals persist in costs.json
- New UI: top bar with search (/ or Ctrl+K) to jump anywhere, a Dashboard (#dashboard), tabs in long panels, Settings (#settings: graphics, streaks, motion, labels, minimap), keyboard shortcut sheet (?), loading screen, one-time welcome card, toasts; phones get a compact bar and bottom-sheet panels
- Look: crosswalks and curbs, textured grass, planters on the plaza, neon accents on the tallest towers, deeper night sky, bloom tuned per time of day; phones start in saver graphics and any device drops to saver if the frame rate stays low
- Weekly pacing: tools/pace.py sizes every session from the latest real usage reading plus logged sessions and ad-hoc tasks (local only, numbers only)
- Tests: pace, treasury, and UI smoke tests (static checks in CI; browser checks on desktop and phone sizes on the build box)

## 2026-10-08 - Overnight: deep links
- Deep links: /agent-city/#market (any building id) or #role=tutor opens that panel and flies there; #overview returns to the skyline
- The address bar follows whatever panel is open, so any view can be copied and shared; closing the panel clears it, and unknown links just open the city
- Quick Council YES (8/10): Grok Bot's notes and the city's own links will point straight at panels from now on

## 2026-10-08 - Message link + Newsroom
- Two-way message link between Grok Bot and Grok Build: a private GitHub issue is the channel and the log; each comment starts with a `[from] [id] [re]` header
- Grok Build side (grok-build/comms/comms.py + new `bot-link` skill): a watcher started as a persistent monitor polls every 10 s with ETag requests (unchanged polls cost no rate limit), prints one line per new message, keeps a cursor, runs once across sessions, backs off when offline, and exits if its session ends; `send` posts the comment through gh and wakes Grok Bot through its inbox webhook (max 1 per 10 s, 60 per hour); `setup --clipboard` reads the webhook config straight from the clipboard so the key never enters a chat; secrets are never printed
- Installer and updater install the link; the global rule gained one line; 28 new tests for the link and 7 for the Newsroom (103 in total), run on ubuntu and macOS
- New role and building: the Reporter works in the Newsroom (red-brick press building with a scrolling ticker next to the Treasury). Every morning it files a 5-8 story digest of LLM, agent, Grok and Grok Build news in news.json, each with its source, why it matters, and the roles it feeds; stories expire after 14 days
- Newsroom stories now feed the Council, Market (Scout), Prompt Workshop, Study Hall (Tutor), and the Grok Build feed's context section
- First digest: 7 stories (Grok Build 1.0.44 and 1.0.46, agent-ready codebases, temperature-0 non-determinism, Reflection Beam, Grok 4.7, Lean-checked math)
- Notice Board: the GitHub Student Developer Pack item is closed (the owner already has it), so nothing needs the owner now

## 2026-10-08 - Cost agents + bulletproof Grok Build link
- Every Grok Build item now carries mandatory `checks` (wiring: references resolve, config loads, lint/build, grok inspect, no duplicates) and 1-2 `tests`; build_data.py refuses to build when one is malformed or more than 3 arrive in a day
- New helper grok-build/city_apply.py does all apply bookkeeping on the owner's machine: process-once log, claims for parallel sessions, max 3 applies an hour, runs checks before and after, rolls back from a snapshot on any failure, commits only the declared files, retries deferred items at most 3 times, reports half-applied items from crashed sessions
- Feed commands are limited to read/test commands (allowlist enforced at both ends), so the public feed cannot run arbitrary code on the owner's machine
- Updater: sha256 manifest with an end marker, verify-then-atomic-replace, scripts wrapped so a truncated download runs nothing, lock for concurrent sessions, 12 s budget, kill switch (`off`) and code pin (`pin`), updates.log; corrupt applied.json is set aside and rebuilt from the log
- Test suite (68 tests) in tests/ and a GitHub Actions workflow on ubuntu and macOS
- New roles in the Treasury: Meter Reader (cost ledger per session from GitHub evidence, with trend) and Optimizer (turns findings into savings); first pass: pushes grew 49 -> 81 KB over 3 sessions, data.js now capped
- Full Council red-team of the interchange: YES 7/10, five fixes made (write flags blocked, daily item cap, updater time budget, crash recovery, immutable change text)

## 2026-10-08 - Grok Build link
- New grok-build/ folder: city-council (the council tailored for coding: repo/files/tests in the Question Crystal, code-specific Full triggers, cheap-tier seats and strongest-tier King), city-apply (review and apply), 7 Grok Build prompts, README
- One-command installer (install.sh) puts the rule, both skills, and a SessionStart hook into ~/.grok; the hook's update.sh pulls fresh files from this repo so changes load automatically; idempotent, backs up anything it replaces, has --uninstall
- build_data.py now writes grok-build/suggestions.md every session: Apply queue (entries with a gb field, stable AC- ids), latest Council verdicts, next best steps, Scout finds for Grok Build
- Review and apply: Grok Build convenes its own council on each new item; YES is implemented, tested, and committed locally, NO is recorded with a reason (~/.grok/agent-city/applied.json, each id once)
- First 2 items in the queue: Prompt Smith's "Done when" rule and the Critic's diff-vs-request review
- Prompt Workshop panel: Grok Build section with the install command (copy button), file links, and the Apply queue
- AGENTS.md: Grok Build section pointing to grok-build/, IDEALS.md, and the suggestions feed

## 2026-10-08 - The Council arrives
- New role: the Council (magenta) decides Notice Board items and city decisions with the council skill; Quick Council (3 seats) for minor, Full Council (14 seats + King + Red Team) for important
- New building: Council Chamber, a round domed chamber with 14 columns next to City Hall; panel explains how it decides and lists verdicts with YES/NO, size, confidence and reason
- IDEALS.md: the user's 7 ideals; the Council reads it before every ruling, each verdict notes its fit, and the Council Chamber shows them
- Library now shows 2 books: agent-city-session and council
- First council session: #33 YES (9/10) and #34 YES (5/10 after the ideals re-check), both built
- Study Hall: Tutor problems carry a "Study this topic" link (today: Paul's Notes, Product and Quotient Rule)
- Notice Board: a one-shot confetti burst when it reaches All clear

## 2026-10-08 - Notice Board cleanup
- Librarian: the agent-city-session skill is saved and is the first book in the Library; its proposal is off the Notice Board
- Toolsmith: adopted Paul's Calc I notes and Python Tutor as clickable links in the Study Hall (Calc I and Intro to CS sections)
- Market: finds show their status (adopted / needs you); approval buttons only on undecided finds. Workshop lists set-up finds with links
- Notice Board: down to 1 optional item (GitHub Student Developer Pack, needs your school verification), now with a clickable link
- Library: skill descriptions written as multi-line YAML now show properly (was showing ">-")
- AGENTS.md: "Never break the live site" publishing rule

## 2026-10-08 - Days 2-4: Catch-up run (9 sessions in one)
- Auditor: split the 50 KB index.html into a small shell + css/style.css + ~25 small plain-script files (one per building), so sessions push only what changed
- Role agents: 12 glowing characters (Inspector, Builder, Scout, Courier, Timekeeper, Tutor, Librarian, Prompt Smith, Toolsmith, Critic, Archivist, Auditor) with speech bubbles of their latest real action; click for history
- activity.json role log merged into data.js; private.json -> private.js (gitignored) for Courier/Timekeeper notes on the local copy only
- New buildings: Clock Tower, Post Office, Study Hall, Prompt Workshop, Workshop, Archive, Review Board, Treasury, Skill Forge, Stats Tower, plaza Notice Board; Town Hall renamed City Hall
- Library: one clickable book per saved skill with SKILL.md preview and a copyable "use my skill" line
- Office: routines board (saved routines on this computer) and a live work board
- Day/night cycle synced to Denver time; T previews day, dusk, night
- Prompt Workshop: 5 copy-paste templates + the Prompt Smith's tip; Skill Forge: 4-step guide + Librarian proposal
- Minimap with click-to-fly; "Go to" building menu
- Notice Board: what needs you + latest build; Stats Tower floors glow with real counts
- Market: freshest-first finds, "new" badges, copyable approval line for the Toolsmith; October tree colors
- First real role pass: Scout (3 finds), Courier, Timekeeper, Tutor (Calc I), Librarian (1 proposal), Prompt Smith, Toolsmith, Inspector, Critic

## 2026-10-08 - Day 1: Foundations
- 3D city scene (three.js via CDN import map, opens by double-clicking index.html)
- Ground, road grid with lane markings, sidewalks, trees, street lamps
- Procedural skyline with lit-window textures, dusk sky gradient, fog, soft shadows, bloom
- Landmarks with floating labels: Library (skills), Office (work), Town Hall (agent roster), Market (scout finds)
- Market (grocery store) with 2 scout figures; panel lists finds from finds.json (empty state until scouts start)
- Library shelves show real saved skills from data.js, or an empty state inviting you to save one
- Low-poly agent figures (one per real agent profile) walking between landmarks; hover/click for name + role
- Controls: orbit/zoom by default, WASD walk mode (Tab toggles), help overlay (H), click landmarks for info panels
- build_data.py regenerates data.js from real skills, agent profiles, finds.json, and this changelog
- Docs: README (controls, finds.json format, session rules), ROADMAP (26-item backlog), AGENTS.md for other AI tools; tools/screenshot.py headless check
