# Agent City for Grok Build

**Problem:** the city's Council, prompts, and suggestions should follow the owner into Grok Build and stay current without copying anything by hand.

## Install (once per machine)

```sh
curl -fsSL https://raw.githubusercontent.com/brandocalricia/agent-city/main/grok-build/install.sh | bash
```

Restart Grok, then `grok inspect`: look for the rule `40-agent-city.md`, the skills `city-council` and `city-apply`, and the hook `agent-city.json`.

| Installed to (`~/.grok`, or `$GROK_HOME`) | What it does |
| --- | --- |
| `rules/40-agent-city.md` | Short global rule, loaded every session: where the city files are, when to run city-apply |
| `skills/city-council/SKILL.md` | `/city-council`: Quick (3 seats) or Full (14 seats + King + Red Team) YES/NO council for code decisions |
| `skills/city-apply/SKILL.md` | `/city-apply`: review and apply. Each new suggestion gets a council verdict; YES is implemented, tested, and committed locally; NO is recorded with a reason |
| `hooks/agent-city.json` | SessionStart hook that runs `agent-city/update.sh` |
| `agent-city/` | `update.sh`, `city_apply.py` (apply helper), `suggestions.md`, `IDEALS.md`, `prompts.md`, `pending.txt`, `applied.log` + `applied.json` (local state, never overwritten), `updates.log`, `backup/` |

Needs `bash`, `curl`, `git`, and `python3` (macOS: Xcode command line tools).

**Updater safety:** runs at most every 30 minutes within a 12 s budget and fails quietly offline. It reads `manifest.txt` (sha256 per file, must end with `end`), downloads each changed file to a temp file, checks hash and marker, then renames it into place, so a partial or corrupt download changes nothing. It writes only the fixed list of Agent City files, never one that lacks the Agent City marker, and never `config.toml`, other rules, skills, or hooks. Both scripts are wrapped in `main()`, so a truncated `curl | bash` runs nothing. A lock keeps parallel sessions from updating at once. Code changes are logged to `agent-city/updates.log`.

**Switches:** `touch ~/.grok/agent-city/off` stops updates and applies; `touch ~/.grok/agent-city/pin` freezes the code (skills, rule, hook, scripts) while the feed still updates.

## How updates flow

1. Every city session (3 a day) runs `build_data.py`, which rebuilds `grok-build/suggestions.md` from Council verdicts, role tips with a `gb` field, Scout finds, and the roadmap.
2. Your next Grok session's SessionStart hook pulls it, plus any new skill or rule text, and counts unprocessed items into `pending.txt`.
3. After your first request is handled, Grok runs `city-apply` on up to 3 items for that repo (or global). Each id is handled once.

**Every item carries checks and tests.** `checks` are wiring checks run before and after the change (references resolve, config loads, lint/typecheck/build, `grok inspect`, no duplicates); `tests` (1-2) must pass after it. Commands come from a read/test allowlist (no writes, no network, no pipes into shells); the city's build rejects anything else, and so does the helper. The helper (`city_apply.py`) refuses items without them, refuses dirty declared files, runs checks before (a failing baseline defers the item, max 3 tries), snapshots the files, runs checks and tests after, rolls back on any failure, and commits only the declared files with `git commit --only`, so your own uncommitted work is never staged or committed. At most 3 applies an hour across all sessions.

Guardrails: never force-push, delete your data, add paid services, change `config.toml` or trust, or send anything externally. It pushes only in repos whose own workflow already pushes.

## Files here

- [prompts.md](prompts.md): 7 copy-paste Grok Build prompts
- [suggestions.md](suggestions.md): the current feed (generated; do not edit)
- [skills/city-council/SKILL.md](skills/city-council/SKILL.md), [skills/city-apply/SKILL.md](skills/city-apply/SKILL.md)
- [../IDEALS.md](../IDEALS.md): the owner's ideals every council reads

## Turn it off

```sh
curl -fsSL https://raw.githubusercontent.com/brandocalricia/agent-city/main/grok-build/install.sh | bash -s -- --uninstall
```

Removes the rule, skills, hook, and updater; keeps `applied.json` and backups. Restart Grok.
