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
| `agent-city/` | `update.sh`, `suggestions.md`, `IDEALS.md`, `prompts.md`, `pending.txt`, `applied.json` (local state, never overwritten), `backup/` |

The updater downloads at most every 30 minutes, fails quietly offline, and only replaces files that are missing or already belong to Agent City. It never touches `config.toml`, other rules, skills, or hooks.

## How updates flow

1. Every city session (3 a day) runs `build_data.py`, which rebuilds `grok-build/suggestions.md` from Council verdicts, role tips with a `gb` field, Scout finds, and the roadmap.
2. Your next Grok session's SessionStart hook pulls it, plus any new skill or rule text, and counts unprocessed items into `pending.txt`.
3. After your first request is handled, Grok runs `city-apply` on up to 3 pending items. Each id is handled once.

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
