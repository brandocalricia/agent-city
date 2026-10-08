# AGENTS.md - guide for AI coding tools (Grok Build, Grok Bot, others)

**What this is:** Agent City, a no-build three.js web app that renders a 3D city of the owner's AI assistants and 13 working roles
(Inspector, Builder, Scout, Courier, Timekeeper, Tutor, Librarian, Prompt Smith, Toolsmith, Critic, Archivist, Council, Auditor).
The Council (Council Chamber, `js/buildings/council.js`) decides Notice Board items and city decisions with the `council` skill: Quick Council (3 seats) for minor,
Full Council (14 seats + King + Red Team) for important. YES is implemented right away, NO closes the item with a reason, user-only actions stay on the board.
The Council reads `IDEALS.md` before every ruling. Log each verdict to activity.json as `{role:'council', action, question, size:'Quick'|'Full', verdict:'YES'|'NO', confidence:1-10, reason, ideals}` (`ideals` = one line on fit, naming any conflict).
Public on GitHub Pages: https://brandocalricia.github.io/agent-city/ (the repo is PUBLIC). Grown ~3 sessions/day.

**Read first:** `IDEALS.md` (the user's ideals; every decision and the Council's every ruling must fit them), then `ROADMAP.md` (top) and the latest `CHANGELOG.md` entry.

**Architecture**
- `index.html` imports three@0.165.0 + addons from jsDelivr in one inline module, puts them on `window.THREE` / `City.lib`,
  then loads the plain scripts listed in `js/manifest.js` in order and calls `City.main()`. Do not convert the city's files to ES modules: they would break `file://`.
- Everything hangs off the global `City`: helpers in `core.js` (`City.box`, `City.simpleBuilding`, `City.sign`, `City.card`, ...), roles in `roles.js`,
  buildings in `js/buildings/<id>.js` via `City.building({ id, name, icon, block:[i,j] | pos:[x,z], role, sub(), build(g) -> roofY, panel() -> html })`.
  Doors auto-face the central plaza. Per-frame work: `City.onFrame((dt, t) => ...)`.
- `data.js` is GENERATED: `window.CITY_DATA = {generatedAt, skills, agents, changelog, finds, activity, routines, ideals}`. Never hand-edit.
- `private.js` (from `private.json`) is gitignored and only requested on file:// or localhost.

**Regenerate data:** `python3 build_data.py` (stdlib only). Off the Grok box the agent-data paths don't exist, so skills/agents/routines come out empty.

**Rules:** one small increment per session; real data only (empty states instead of fake data); personal email/calendar content,
sender names, and amounts never go into pushed files; push only changed files; bump `City.version` in `js/manifest.js`; keep it fast on laptops
(merge/instance geometry, no extra dynamic lights, respect the `Q` saver toggle).

## Never break the live site
The site at https://brandocalricia.github.io/agent-city/ must keep working while work is in progress. Build and verify locally first; publish all changed files in one commit. If a push must be split, push new files first and the files that reference them (index.html, js/manifest.js, data.js) last. After publishing, load the live URL and confirm no failed requests.
