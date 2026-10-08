# Agent City - Changelog

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
