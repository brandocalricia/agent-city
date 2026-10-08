# Agent City - Changelog

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
