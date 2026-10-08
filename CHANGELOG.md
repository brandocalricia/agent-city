# Agent City - Changelog

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
