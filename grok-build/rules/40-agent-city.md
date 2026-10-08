# Agent City (installed by agent-city/grok-build/install.sh)

The owner's Agent City (https://brandocalricia.github.io/agent-city/) sends Grok Build suggestions. Files live in `~/.grok/agent-city/`: `suggestions.md` (feed), `IDEALS.md` (the owner's ideals), `prompts.md`, `pending.txt`, `applied.json` (local state). A SessionStart hook refreshes them.

- Decisions the owner hands to "the council" use the `city-council` skill and fit IDEALS.md.
- Review and apply: handle the owner's request first. Then, once per interactive session, if the first line of `~/.grok/agent-city/pending.txt` is a number above 0, run the `city-apply` skill (at most 3 items, council-gated, local commits only). Do not read suggestions.md otherwise.
- Never force-push, delete the owner's data, add paid services, or send anything externally because of a city item.
