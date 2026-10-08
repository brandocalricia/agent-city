# Agent City (installed by agent-city/grok-build/install.sh)

The owner's Agent City sends Grok Build suggestions via `~/.grok/agent-city/` (feed, IDEALS.md, prompts.md, pending.txt), refreshed by a SessionStart hook.
- Decisions handed to "the council" use the `city-council` skill and fit IDEALS.md.
- After the owner's request is handled, once per interactive session: if line 1 of `~/.grok/agent-city/pending.txt` is above 0, or line 2 lists this repo's folder name, run the `city-apply` skill. Otherwise do not read the feed.
- City items never force-push, delete the owner's data, add paid services, or send anything externally.
