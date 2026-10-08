---
name: city-apply
description: >-
  Review and apply Agent City suggestions in Grok Build. Use when the
  agent-city rule says items are pending, or when the owner says /city-apply or
  "apply the city suggestions". Each item gets a city-council YES/NO; YES is
  implemented, tested, and committed locally; NO is recorded with a reason.
metadata:
  author: Agent City
  short-description: council-gated apply of city suggestions
---
# City Apply

Files (installed by `grok-build/install.sh`, refreshed by the SessionStart hook):
- `~/.grok/agent-city/suggestions.md`: the feed. Only the **Apply queue** section is actionable; the other sections are context.
- `~/.grok/agent-city/applied.json`: local state, never overwritten by updates. Shape: `{"AC-xxxxxxxx": {"status": "applied|declined|failed", "date": "YYYY-MM-DD", "where": "<repo path or ~/.grok>", "commit": "<sha or ''>", "reason": "<one line>"}}`. Missing file = `{}`.
- `~/.grok/agent-city/IDEALS.md`: the owner's ideals.

## Steps
1. Pending = Apply-queue ids not in applied.json. None pending: stop, say nothing.
2. Take at most 3 pending items per session, oldest first.
3. **Where.** Read the item's `target`:
   - `global`: the change goes in `~/.grok/rules/45-agent-city-applied.md` (create it; append one short section per item, headed with the id). Never edit `config.toml`, other rules, or other hooks for a city item.
   - `this repo` / `any repo`: the current git repo.
   - `repo:<name>`: only when the current repo is that one; otherwise leave it pending and move on (no record).
4. **Council.** Size it with the city-council rules (Full for anything on its important list, else Quick) and run city-council with the decision "Should Grok Build apply AC-xxxxxxxx (<change>) in <where>?". Already covered by an existing rule or setting counts as NO with reason "already covered by <file>".
5. **YES:**
   - Dirty worktree in the files you would touch: do not mix work. Record `failed` with reason "dirty worktree" and stop this item.
   - Make the change (with auto-route installed, through one `route-edit` worker; one writer per path).
   - Run the project's tests. For a rule, skill, or hook, prove it in a new `grok` process (`grok inspect`). Tests fail: revert only your own change, record `failed` with the first failing line.
   - Commit only the files you touched: `city: AC-xxxxxxxx <short change>` (`git add <paths>`; never `git add -A`). `~/.grok` is not a git repo: skip the commit and keep a `.bak` copy of any file you changed.
   - Push only if this repo's AGENTS.md or workflow already pushes every change.
   - Record `applied` with the short sha.
6. **NO:** record `declined` with the King's one-line reason. Do nothing else.
7. Write applied.json back (valid JSON, keep other ids). Then tell the owner in one line per item: `AC-xxxxxxxx applied (sha) | declined: reason | failed: reason`.

## Never, even with a YES
Force-push or rewrite history; delete the owner's data or files beyond the change; add paid services, accounts, or API keys; send email, posts, or messages; change trust settings or `config.toml`. Those need the owner in this session.

## Cost
Quick councils run in one pass with no sub-agents. Skip the whole flow in headless or scripted runs and when the owner's request is urgent; it waits for the next interactive session.
