# Agent City - Changelog

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
