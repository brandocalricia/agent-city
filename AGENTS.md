# AGENTS.md - guide for AI coding tools (Grok Build, Grok Bot, others)

**What this is:** Agent City, a no-build three.js web app (`index.html`) that renders a 3D city visualizing
Brandon's AI assistants: Library = saved skills, Office = work log, Town Hall = agent roster, Market = scout finds.
It is grown in small daily increments (about 3 sessions/day).

**How files fit together**
- `index.html` contains all code (CSS, an import map for three@0.165.0 from jsDelivr, and one inline ES module). Landmarks are built in the `builders` object; panels in `PANELS`; layout in `LANDMARKS`.
- `data.js` is GENERATED (never hand-edit). It sets `window.CITY_DATA = {generatedAt, skills[], agents[], changelog[], finds[]}` and is loaded via a plain `<script>` so the page works from `file://` (no `fetch`).
- `build_data.py` builds `data.js` from real sources: `/home/box/agent-data/workflows/*/SKILL.md` (frontmatter `name`, `description`), `/home/box/agent-data/agents/*/profile.json` (`name`, `title`, ...), `finds.json`, and `CHANGELOG.md`. Missing sources yield empty arrays; the UI shows empty states. Never fabricate entries.
- `finds.json`: array of `{date, title, url, source, why_useful}` (format in README).
- `tools/screenshot.py`: headless render check; serve the folder on 127.0.0.1:8765 first.

**Regenerate data:** `python3 build_data.py` (stdlib only). Off the Grok box, the agent-data paths won't exist, so it will produce empty skills/agents; that's expected.

**Session rule:** ONE small increment per session (top unchecked `ROADMAP.md` item), keep it opening by double-click,
regenerate `data.js`, take and inspect a screenshot, add a dated `CHANGELOG.md` entry, tick `ROADMAP.md`. Keep it fast on laptops
(merge/instance geometry, avoid extra lights, respect the `Q` laptop-saver toggle).
