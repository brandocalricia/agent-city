# Agent City

A 3D city in your browser where your AI assistants and their working roles live and show their real work.
Live (public): https://brandocalricia.github.io/agent-city/ · Local: double-click `index.html`.

## What's in the city
| Building | Role | Shows |
|---|---|---|
| 🏛 City Hall | 🔍 Inspector | assistants + role directory; checks the city loads |
| 🏢 Office | 🔨 Builder | routines board, work log |
| 🛒 Market | 🧭 Scout | finds (freshest first), approval lines |
| 📚 Library | 📖 Librarian | saved skills as books; skill proposals |
| ✉️ Post Office | ✉️ Courier | email flags (**local copy only**) |
| ⏰ Clock Tower | ⏰ Timekeeper | calendar notes (**local copy only**) |
| 🎓 Study Hall | 🎓 Tutor | practice problem with hidden solution |
| ✍️ Prompt Workshop | ✍️ Prompt Smith | prompting tips + copy-paste templates |
| 🛠 Workshop | 🛠 Toolsmith | works only on approved finds |
| 🧐 Review Board | 🧐 Critic | checks of everyone's output |
| 🗄 Archive | 🗄 Archivist | Sunday weekly summary |
| 🧾 Treasury | 🧾 Auditor | token-saving changes (estimates labeled) |
| ⚒ Skill Forge, 📊 Stats Tower, 📌 Notice Board | - | skill guide, real counts, what needs you |

## Controls
Drag/right-drag/scroll to orbit/pan/zoom · click anything to open it · `1`-`4` Library/Office/City Hall/Market · `0` overview ·
"Go to" menu or minimap click to fly · `Tab` walk mode (`WASD`, mouse, `Shift`, `E`) · `T` time of day · `Q` laptop saver · `H` help · `Esc` close.

## Files
- `index.html`: small shell + loader. three.js comes from jsDelivr as ES modules; the city's own code is **plain scripts**
  (`js/manifest.js` lists them) because local ES-module files are blocked on `file://`. Works by double-click and on GitHub Pages.
- `css/style.css`; `js/core.js` (helpers, renderer), `js/roles.js`, `js/world.js`, `js/daynight.js`, `js/agents.js`, `js/panels.js`, `js/minimap.js`, `js/ui.js`, `js/main.js`
- `js/buildings/*.js`: one file per building (`City.building({...})`). New building = new file + add its name in `js/manifest.js`.
- `data.js`: **generated** by `build_data.py` (skills, agent profiles, routines, `finds.json`, `activity.json`, `CHANGELOG.md`).
- `activity.json`: append-only role log `[{date, session, role, action, details, link?, needs_user?, course?, solution?}]`. Real actions only.
- `finds.json`: `[{date, title, url, source, why_useful, status: "new"|"approved"}]`. Only things actually found.
- `private.json` -> `private.js`: **gitignored, never pushed.** Courier/Timekeeper/Auditor notes and private notices; loaded only on the local copy
  (`file://` or localhost; add `?public` to preview the public view). The public site shows "Private - visible on the local copy only".
- `tools/screenshot.py`: headless render check.

## Rules for future sessions
1. One small increment per session: the top unchecked `ROADMAP.md` item (unless the user asks otherwise); add 2 new ideas.
2. Keep it working by double-click and on Pages. No build step, no `fetch()`.
3. Log each role's real actions in `activity.json`; personal email/calendar details go only in `private.json`.
4. `python3 build_data.py`, then `python3 -m http.server 8765 --bind 127.0.0.1 &` and `python tools/screenshot.py <name>`; look at the shots.
5. Update `CHANGELOG.md` + `ROADMAP.md`. Before pushing, grep pushed files for emails, senders, amounts, event names.
6. Push **only the files you changed** (usually 1-4 small files + data.js) in one commit. Bump `version` in `js/manifest.js` to bust the Pages cache.
