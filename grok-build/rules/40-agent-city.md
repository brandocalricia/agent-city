# Agent City (installed by agent-city/grok-build/install.sh)

The owner's Agent City sends Grok Build suggestions via `~/.grok/agent-city/` (feed, IDEALS.md, prompts.md, pending.txt), refreshed by a SessionStart hook.
- Decisions handed to "the council" use the `city-council` skill and fit IDEALS.md.
- After the owner's request is handled, once per interactive session: if line 1 of `~/.grok/agent-city/pending.txt` is above 0, or line 2 lists this repo's folder name, run the `city-apply` skill. Otherwise do not read the feed.
- Message link: early in each interactive session, if `~/.grok/agent-city/comms.py` exists and `~/.grok/agent-city/bot-webhook.env` exists (link configured; webhook optional — thread-only is the default) and `gh` is signed in (`gh auth token` works), start `python3 -u ~/.grok/agent-city/comms.py watch` with the monitor tool (persistent: true, description "Agent City"); it resolves the Channel PR by title (creates branch `channel` + PR + hello if missing), exits at once if another session runs it. Handle its `[agent-city]` lines with the `bot-link` skill.
- City items never force-push, delete the owner's data, add paid services, or send anything externally (the bot-link thread is the one exception).
