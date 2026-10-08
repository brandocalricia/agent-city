# Agent City - Roadmap

Prioritized backlog. Each item = one short session. Take the top unchecked item unless the user asks for something else.
Legend: [x] done · [ ] todo · (W) wow factor · (U) useful

## Day 1 (2026-10-08) - done
- [x] Ground, road grid, lane markings, sidewalks, trees, street lamps
- [x] Procedural skyline with lit windows, dusk sky, fog, shadows, bloom
- [x] Landmarks with floating labels: Library, Office, Town Hall, Market
- [x] Agent figures from real profiles walking between landmarks; hover/click info
- [x] Market with 2 scout figures; finds.json -> data.js -> Market panel (empty state)
- [x] Orbit + WASD walk mode, help overlay, fly-to buttons, quality toggle, info panels
- [x] build_data.py (skills, agents, changelog, finds), headless screenshot tool

## Backlog (top = next)
1. [ ] (U) Library shelf per real skill: 3D books you can click to open that skill's description and full SKILL.md preview
2. [ ] (U) Office routines board: show the agents' saved routines/schedules and a recent work log on the tower wall and in the panel (extend build_data.py)
3. [ ] (W) Day/night cycle synced to real Denver time (sun position, sky colors, window lights brighter at night)
4. [ ] (U) Prompt Workshop building: tips and copy-paste templates for prompting agents well (clear goal, context, output format, constraints)
5. [ ] (U) Skill Forge building: step-by-step guide to turning a repeated task into a saved skill, with an example and a "say this to Grok Bot" button that copies the phrase
6. [ ] (U) Market "freshness" shelf: finds sorted by age, with new (<3 days) glowing and stale (>30 days) dimmed, plus a "new since last visit" badge (localStorage)
7. [ ] (W) Minimap in a corner with landmark icons, agent dots, and click-to-fly
8. [ ] (U) Notice Board in the plaza: pinned reminders and the latest CHANGELOG entry, clickable
9. [ ] (U) Stats Tower: a tower whose floors light up with counts (skills, agents, finds, sessions, days built)
10. [ ] (W) Agents follow sidewalks/crosswalks instead of cutting corners; idle animations at landmarks (reading at Library, typing at Office)
11. [ ] (W) Weather system: rain/snow particles with toggle (snow for Denver winters), wet-road reflections
12. [ ] (W) Sounds toggle: soft ambient city loop + fountain + click blips (off by default, WebAudio generated, no files)
13. [ ] (W) Cars driving along roads with headlights (instanced, cheap)
14. [ ] (U) Search box: type a skill/find/agent name, camera flies there and opens its panel
15. [ ] (U) "Copy prompt" buttons in panels (e.g. "Use skill X on ...") that copy a ready-to-paste instruction for Grok Bot
16. [ ] (W) Particle effects: sparkles when a new skill or find appears since last visit (compare to localStorage)
17. [ ] (U) City timeline in Town Hall: every CHANGELOG entry as a scrollable history with screenshots
18. [ ] (W) Lights in windows flicker on/off slowly over time; occasional office-tower window patterns
19. [ ] (U) Agent detail cards: per-agent stats (skills authored, recent tasks) when data is available
20. [ ] (W) Seasonal decorations driven by date (autumn leaf colors now, snow caps in winter, DU crimson & gold flags on game days)
21. [ ] (U) Study Hall building for Brandon's classes: quick links/tips per course pulled from saved skills (only real data)
22. [ ] (W) Photo mode: hide UI, cinematic slow orbit, save PNG
23. [ ] (U) Mobile/touch controls (virtual joystick, tap to open)
24. [ ] (W) Water: animated fountain shader + a river/park on the city edge
25. [ ] (U) Performance pass: frustum-cull labels, LOD for far buildings, FPS counter in laptop-saver mode
26. [ ] (W) Hot-air balloon/drone tour: one-click guided tour of all landmarks with captions
