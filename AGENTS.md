# AGENTS.md - guide for AI coding tools (Grok Build, Grok Bot, others)

**What this is:** Agent City, a no-build three.js web app that renders a 3D city of the owner's AI assistants and 15 working roles
(Inspector, Builder, Scout, Courier, Timekeeper, Tutor, Librarian, Prompt Smith, Toolsmith, Critic, Archivist, Council, Auditor, Meter Reader, Optimizer).
The Council (Council Chamber, `js/buildings/council.js`) decides Notice Board items and city decisions with the `council` skill: Quick Council (3 seats) for minor,
Full Council (14 seats + King + Red Team) for important. YES is implemented right away, NO closes the item with a reason, user-only actions stay on the board.
The Council reads `IDEALS.md` before every ruling. Log each verdict to activity.json as `{role:'council', action, question, size:'Quick'|'Full', verdict:'YES'|'NO', confidence:1-10, reason, ideals}` (`ideals` = one line on fit, naming any conflict).
Public on GitHub Pages: https://brandocalricia.github.io/agent-city/ (the repo is PUBLIC). Grown ~3 sessions/day.

**Grok Build:** when you work in this repo, read `grok-build/README.md`. Decisions handed to "the council" use `grok-build/skills/city-council/SKILL.md` and fit `IDEALS.md`.
Review and apply: `grok-build/suggestions.md` (generated, never hand-edit) is the city's feed for Grok Build; its Apply queue is handled by `grok-build/skills/city-apply/SKILL.md`
(city-council YES -> implement, test, commit locally; NO -> record a one-line reason; state in `~/.grok/agent-city/applied.json`, each id once).
Never force-push, delete the owner's data, add paid services, or send anything externally because of a city item. Prompts: `grok-build/prompts.md`.
To send Grok Build a suggestion, give an activity.json or finds.json entry a `gb` field:
`{change, target: 'global'|'repo:<name>', size: 'Quick'|'Full', why, checks: [...], tests: [...]}`. `checks` (2+) are wiring checks run before and after
(references resolve, config loads, lint/typecheck/build, `grok inspect`, no duplicates); `tests` (1-2) must pass after. At least one of each starts with `$ `
(a command the helper runs; read/test commands only, see `command_problem` in `grok-build/city_apply.py`; placeholders `{id}` `{rules_file}` `{repo}`
`{test_cmd}` `{lint_cmd}` `{build_cmd}`). Max 3 gb items per day. Never edit a published `change` text (its id is a hash of it); add a new item instead.
`build_data.py` exits 1 and writes nothing when a gb entry is malformed: fix it before publishing.

**Cost agents (evening session, skip when nothing is new):** the Meter Reader adds the session's push size to `costs.json` (`ledger`: bytes read from
GitHub at the commit, tokens ~ bytes/4); the Optimizer turns ledger and Auditor findings into `costs.json` `savings`, and terminal-setup savings into gb items.
Both log one activity.json line; the Treasury shows the ledger and savings.

**Tests:** `python3 -m unittest discover -s tests` (stdlib; build_data, install/update, city_apply). Run before every publish; CI runs it on ubuntu and macOS.
After changing anything in `grok-build/`, run `python3 build_data.py` so `grok-build/manifest.txt` (sha256 per installed file) matches, and push the manifest
in the same commit: a stale manifest makes owners' updaters reject the new files.

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
