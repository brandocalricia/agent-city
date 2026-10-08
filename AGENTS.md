# AGENTS.md - guide for AI coding tools (Grok Build, Grok Bot, others)

**What this is:** Agent City, a no-build three.js web app that renders a 3D city of the owner's AI assistants and 16 working roles
(Inspector, Builder, Scout, Courier, Timekeeper, Tutor, Librarian, Prompt Smith, Toolsmith, Critic, Archivist, Council, Auditor, Meter Reader, Optimizer, Reporter).
The Council lives in Town Hall (Council) at the center of the city (`js/buildings/townhall.js`; verdict view and old-link redirects in `js/buildings/council.js`) and decides Notice Board items and city decisions with the `council` skill: Quick Council (3 seats) for minor,
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
Each ledger entry also carries `saved_kb`/`saved_tokens` (measured savings, method in `saved_method`); `price` states the $/1M-token basis and source.
Never delete ledger entries without adding their totals to `archived`: `tools/treasury.py` sums ledger + archived into the Treasury's lifetime totals.
Both log one activity.json line; the Treasury shows lifetime savings, cost per build, the weekly limit vs plan, the trend, and the biggest savings.

**Newsroom (Reporter, every morning; evenings only a quick check for big breaking news):** reads the latest LLM, AI agent, Grok/xAI and Grok Build
news (x connector `search_news`/`get_news`/`search_posts_all`, plus WebSearch; primary sources such as the Grok Build changelog first) and appends
5-8 stories for the day to `news.json`: `{date, title, url (https, the source), source, why (one line: why it matters for the city or Grok Build),
tag: model|agents|grok|grok-build|technique|tokens|tools|school, for: [council|scout|promptsmith|tutor|gb]}`. Label X News stories "X News (summary of
posts)"; never invent a story or a number. `for` routes a story into that role's panel ("From the Newsroom") and, for `gb`, into the context part of
`grok-build/suggestions.md`; the Council, Scout, Prompt Smith, and Tutor read their routed stories before acting. Something actionable for Grok Build
becomes a normal gb item (with checks and tests, within the 3-a-day cap). Delete stories older than 14 days from news.json (build_data.py also drops them
from data.js). Max 8 stories per day; a malformed story stops the build like a malformed gb item. Log one activity.json line (`role: 'reporter'`).

**Message link (Grok Bot <-> Grok Build):** a private thread, issue #1 of `brandocalricia/agent-city-comms` (never copy its contents into this public repo).
Each message is one comment whose first line is `[from:grok-bot|grok-build] [id:<short id>] [re:<id or ->]`, then the body. Grok Bot posts with the GitHub
connector (`add_issue_comment`), ids `b` + 5-6 base36 chars; Grok Build replies with `grok-build/comms/comms.py send` (comment via `gh` + a POST of
`{id, re, text, from, comment_url}` to Grok Bot's "Grok Build inbox" routine webhook). Grok Build's watcher (`comms.py watch`, a persistent monitor started
by the global rule) polls every 10 s with ETag/If-None-Match and prints one line per new grok-bot message; the `bot-link` skill says how to handle it
(questions answered directly, code changes go through city-council, never secrets or external sends). Dedupe by comment id and message id, ignore your own
messages, reply once, never reply to plain acknowledgements; Grok Build's send is capped at 1 per 10 s and 60 per hour. Webhook URL and sender key live
only in `~/.grok/agent-city/bot-webhook.env` on the owner's Mac (chmod 600), never in any repo or message.

**Pacing (every session, first):** `python3 tools/pace.py` reads the local, gitignored `budget.json` (latest real usage reading + logged `sessions` and `adhoc`
entries since) and prints the size for this session (L/M/S/minimal/skip). Size the session from it, and log the session in `budget.json` `sessions` at the end;
ad-hoc work for the owner goes in `adhoc`. It prints numbers only; never publish budget.json.

**Tests:** `python3 -m unittest discover -s tests` (stdlib; build_data incl. news, install/update, city_apply, comms, pace, treasury, UI static checks;
the UI browser smoke tests run where Playwright + Chrome exist and skip elsewhere). Run before every publish; CI runs it on ubuntu and macOS.
After changing anything in `grok-build/`, run `python3 build_data.py` so `grok-build/manifest.txt` (sha256 per installed file) matches, and push the manifest
in the same commit: a stale manifest makes owners' updaters reject the new files.

**Read first:** `IDEALS.md` (the user's ideals; every decision and the Council's every ruling must fit them), then `ROADMAP.md` (top) and the latest `CHANGELOG.md` entry.

**Architecture**
- `index.html` imports three@0.165.0 + addons from jsDelivr in one inline module, puts them on `window.THREE` / `City.lib`,
  then loads the plain scripts listed in `js/manifest.js` in order and calls `City.main()`. Do not convert the city's files to ES modules: they would break `file://`.
- Everything hangs off the global `City`: helpers in `core.js` (`City.box`, `City.simpleBuilding`, `City.sign`, `City.card`, ...), roles in `roles.js`,
  buildings in `js/buildings/<id>.js` via `City.building({ id, name, icon, block:[i,j] | pos:[x,z], role, sub(), build(g) -> roofY, panel() -> html })`.
  Doors auto-face the central plaza, where Town Hall (Council) stands as the hub (`City.HUB` = its beacon). Per-frame work: `City.onFrame((dt, t) => ...)`.
- UI: `hud.js` (top bar, search, dashboard and settings views via `City.registerView`, shortcuts, welcome card, toasts; settings in localStorage),
  `visuals.js` (crosswalks, textures, neon accents, time-of-day bloom, automatic quality), `streaks.js` (`City.streaks.fire(roleId)`: neon trail from the
  role's building to Town Hall, max 4 at once, off under reduced motion). Panels with 3+ `<h4>` sections get tabs automatically.
- `data.js` is GENERATED: `window.CITY_DATA = {generatedAt, skills, agents, changelog, finds, activity, totals, routines, ideals, costs, news, treasury, gb}`. Never hand-edit.
- `private.js` (from `private.json`) is gitignored and only requested on file:// or localhost.

**Deep links:** `#<building id>` (e.g. `#townhall`, `#market`), `#role=<role id>`, `#overview`, `#dashboard`, `#settings` open that view (`js/deeplink.js`); old anchors `#council` and `#cityhall` redirect to `#townhall`. Use them when linking the owner to something in the city.

**Regenerate data:** `python3 build_data.py` (stdlib only). Off the Grok box the agent-data paths don't exist, so skills/agents/routines come out empty.

**Rules:** one small increment per session; real data only (empty states instead of fake data); personal email/calendar content,
sender names, and amounts never go into pushed files; push only changed files; bump `City.version` in `js/manifest.js`; keep it fast on laptops
(merge/instance geometry, no extra dynamic lights, respect the `Q` saver toggle).

## Never break the live site
The site at https://brandocalricia.github.io/agent-city/ must keep working while work is in progress. Build and verify locally first; publish all changed files in one commit. If a push must be split, push new files first and the files that reference them (index.html, js/manifest.js, data.js) last. After publishing, load the live URL and confirm no failed requests.
