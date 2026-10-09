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

**Newsroom (Reporter):** full run at the **8:49 AM** session (append 5-8 stories for the day); light check at the **8:49 PM** session (at most 2 breaking stories, or skip). Reads the latest LLM, AI agent, Grok/xAI and Grok Build
news (x connector `search_news`/`get_news`/`search_posts_all`, plus WebSearch; primary sources such as the Grok Build changelog first) and appends
stories to `news.json`: `{date, title, url (https, the source), source, why (one line: why it matters for the city or Grok Build),
tag: model|agents|grok|grok-build|technique|tokens|tools|school, for: [council|scout|promptsmith|tutor|gb]}`. Label X News stories "X News (summary of
posts)"; never invent a story or a number. `for` routes a story into that role's panel ("From the Newsroom") and, for `gb`, into the context part of
`grok-build/suggestions.md`; the Council, Scout, Prompt Smith, and Tutor read their routed stories before acting. Something actionable for Grok Build
becomes a normal gb item (with checks and tests, within the 3-a-day cap). Delete stories older than 14 days from news.json (build_data.py also drops them
from data.js). Max 8 stories per day; a malformed story stops the build like a malformed gb item. Log one activity.json line (`role: 'reporter'`).

**Free-lane drafting (this Mac):** Grok Bot cannot reach the local free router, so these jobs are drafted here and Grok Bot only reviews and publishes: Newsroom drafts, Scout finds, tests, docs/CHANGELOG/ROADMAP drafts, first-pass review, Inspector checks, and data refreshes. Drafts use auto/offline. Code uses auto/coding. Each delivery is a small branch plus the lane and model that produced it. A fact needs an https source that was fetched. If a free draft fails a test or adds a fact that was not in the source, redo it on another free lane. Grok is the last resort. Measured in/out counts per role go in `data/omniroute.json` under `routed_free_by_role` (`free_in`, `free_out`, `grok_in`, `grok_out`). That public file must not contain the substring `token`.

**Message link (Grok Bot <-> Grok Build):** a private thread — the open **pull request** titled **Channel** in `brandocalricia/agent-city-comms` (find by title, never hard-code the number; never copy its contents into this public repo). Conversation comments on that PR are the log (`issues/{n}/comments` works for PRs).
Grok Bot, at the start of every session, reads new grok-build comments (dedupe by message id; last-seen id in local gitignored `channel-seen.json`), handles them, and replies with the GitHub connector (`add_issue_comment` / PR comment). Every grok-bot comment's first line MUST be `[from:grok-bot] [id:<b…>] [re:<id or ->]` — the `[from:grok-bot]` prefix is required so the PR-comment wake listener can exit immediately. Grok Build's `comms.py` (setup/watch/send) resolves the same PR by title via `gh` (creates branch `channel` + `channel/README.md` + `gh pr create --title Channel` and posts a first grok-build hello if missing), then `send` posts the comment (optional webhook POST of `{id, re, text, from, comment_url}` only when configured). Thread-only is the default: `comms.py setup` with no URL/key writes `bot-webhook.env` with `AGENT_CITY_WEBHOOK=off`. Grok Build's watcher (`comms.py watch`, auto-started by the global rule once `bot-webhook.env` exists and `gh` is signed in — webhook not required) polls every 10 s with ETag/If-None-Match and prints one line per new grok-bot message; the `bot-link` skill says how to handle it
(questions answered directly, code changes go through city-council, never secrets or external sends). Deduplicate by comment id and message id, ignore your own
messages, reply once, never reply to plain acknowledgements; Grok Build's send is capped at 1 per 10 s and 60 per hour. Optional webhook URL/key (if the panel ever shows them) go into `comms.py setup --url/--key` and live only in `~/.grok/agent-city/bot-webhook.env` on the owner's Mac (chmod 600, never echoed), never in any repo or message.


**Pacing (every session, first):** `python3 tools/pace.py` reads the local, gitignored `budget.json` (latest real usage reading + logged `sessions` and `adhoc`
entries since, from every Grok Bot — Agent City, Math Tutor, …) and prints the size for this session (L/M/S/minimal/skip) plus a per-source breakdown
(sessions / Agent City ad-hoc / math-tutor / other reading-drift). Size the session from it, and log the session in `budget.json` `sessions` at the end;
ad-hoc work goes in `adhoc` with a `source`. Evening reports include the breakdown. Numbers only; never publish budget.json.

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
- Tutor entries carry `details` (problem), `solution`, and a short `answer` (final expression in x when possible) plus optional `accept` (other accepted forms) for the Study Hall's local check (`City.checkAnswer` in `js/buildings/studyhall.js`).
- `data.js` is GENERATED: `window.CITY_DATA = {generatedAt, skills, agents, changelog, finds, activity, totals, routines, ideals, costs, news, treasury, gb}`. Never hand-edit.
- `private.js` (from `private.json`) is gitignored and only requested on file:// or localhost.

**Deep links:** `#<building id>` (e.g. `#townhall`, `#market`), `#role=<role id>`, `#overview`, `#dashboard`, `#settings` open that view (`js/deeplink.js`); old anchors `#council` and `#cityhall` redirect to `#townhall`. Use them when linking the owner to something in the city.

**Regenerate data:** `python3 build_data.py` (stdlib only). Off the Grok box the agent-data paths don't exist, so skills/agents/routines come out empty.

**Rules:** one small increment per session; real data only (empty states instead of fake data); personal email/calendar content,
sender names, and amounts never go into pushed files; push only changed files; bump `City.version` in `js/manifest.js`; keep it fast on laptops
(merge/instance geometry, no extra dynamic lights, respect the `Q` saver toggle).

## Never break the live site
The site at https://brandocalricia.github.io/agent-city/ must keep working while work is in progress. Build and verify locally first. **One publish method only:** always use the `publish` branch (never push straight to `main` from a session). Create `publish` from main, push the changed files in any number of commits (the live site only serves main), and put `[publish]` in the LAST commit message. `.github/workflows/publish.yml` then runs the tests, refuses if main changed meanwhile in files the branch differs on, regenerates data.js and the Grok Build feed (off the box, build_data.py keeps the committed data.js's skills, agents and routines), moves main to the branch's files in ONE commit, asks Pages to rebuild, and deletes the branch. A session that stops partway leaves main untouched. After the Action finishes, load the live URL and confirm no failed requests. At the start of each session, compare the live `City.version` with the local one and finish any stalled publish first.
