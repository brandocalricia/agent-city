# Agent City

A 3D, explorable city in your browser that visualizes your AI assistants and their real work:
the **Library** holds your saved skills, the **Office** shows work being done, the **Town Hall** keeps the
agent roster, and the **Market** is where scout agents bring back useful tools they find.

## Open it
Double-click `index.html` (Chrome, Edge, Firefox, or Safari). No install or server needed.
It needs an internet connection the first time, because three.js loads from a CDN.

## Controls
| Action | How |
|---|---|
| Orbit / pan / zoom | drag · right-drag · scroll |
| Open a building, agent, or label | click it |
| Fly to landmark | `1` Library · `2` Office · `3` Town Hall · `4` Market · `0` overview |
| Walk mode | `Tab` toggles · `WASD` move · mouse look · `Shift` run · `E` open what you're looking at |
| Help overlay | `H` |
| Quality (laptop saver: no bloom/shadows) | `Q` |
| Close panel | `Esc` |

## Files
- `index.html`: the whole app (three.js via import map, inline module).
- `data.js`: **generated** by `build_data.py`; defines `window.CITY_DATA`. Loaded with a plain `<script>` so it works on `file://`.
- `build_data.py`: reads real state on the box: skills in `/home/box/agent-data/workflows/*/SKILL.md`,
  agent profiles in `/home/box/agent-data/agents/*/profile.json`, `finds.json`, and `CHANGELOG.md`. It never invents data.
- `finds.json`: Market scout finds (see below).
- `tools/screenshot.py`: headless render check (playwright + Chrome).
- `ROADMAP.md`, `CHANGELOG.md`, `AGENTS.md`.

## finds.json format (Market)
A JSON array; newest first is not required (build_data.py sorts by date). Entries without a `title` are skipped.
```json
[
  {
    "date": "2026-10-09",
    "title": "Example tool name",
    "url": "https://example.com",
    "source": "where it was found (site, newsletter, X post...)",
    "why_useful": "one or two sentences on why it helps Brandon"
  }
]
```
Starts as `[]`, so the Market shows "Scouts start shopping tomorrow". Only add things that were actually found.

## Rules for future build sessions
1. **One small increment per session**: take the top unchecked item in `ROADMAP.md` (unless the user asked for something else).
2. **Keep it working**: it must still open by double-clicking `index.html`; no build step, no `fetch()`.
3. Run `python3 build_data.py` to regenerate `data.js`.
4. Take a screenshot: `python3 -m http.server 8765 --bind 127.0.0.1 &` then `python tools/screenshot.py dayN`, look at it, and fix any blank canvas or console errors.
5. Update `CHANGELOG.md` (dated entry) and tick the item in `ROADMAP.md`, then re-zip / push.
6. Keep sessions token-light: the user wants plenty left for real work.
