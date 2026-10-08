---
name: city-apply
description: >-
  Review and apply Agent City suggestions in Grok Build. Use when the
  agent-city rule says items are pending, or when the owner says /city-apply or
  "apply the city suggestions". Each item gets a city-council YES/NO; YES is
  applied with mandatory checks and tests, committed locally, and rolled back
  if anything fails; NO is recorded with a reason.
metadata:
  author: Agent City
  short-description: council-gated, test-gated apply of city suggestions
---
# City Apply

All bookkeeping goes through the helper; never edit `applied.json`, claims, or journals by hand.
`H="python3 $HOME/.grok/agent-city/city_apply.py"` (state in `~/.grok/agent-city/`; `$GROK_HOME` if set).

## Steps
0. Helper missing (fresh upgrade): run `bash ~/.grok/agent-city/update.sh --force` once; still missing: stop.
1. `$H next --repo "$PWD"` returns up to 3 items actionable here (global items, plus `repo:<name>` items when this repo's folder is that name). Empty: stop and say nothing. Never read suggestions.md yourself; `next` gives you each item's change, why, checks, and tests. Items missing checks or tests are skipped by the helper. If it lists `unfinished` items (a session died mid-apply), tell the owner in one line and run `$H rollback <id>` only after `git diff` shows nothing but that item's change in its paths.
2. For each item, run city-council (Full if it hits the council's important list, else Quick) on "Should Grok Build apply <id> (<change>) here?". Give the council the item's checks and tests. Already covered by an existing rule or file = NO, reason "already covered by <file>".
3. **NO:** `$H finish <id> --status declined --reason "<King's one line>"`. Next item.
4. **YES:**
   1. `$H begin <id> --repo "$PWD" --paths <every file you will create, edit, or delete>` (global items: no `--paths`; they may only touch `~/.grok/rules/45-agent-city-applied.md`, one `## <id>` section each). Begin refuses dirty declared paths, claimed items, items already processed, and a 4th item within an hour. A refusal is final for this session: say why in one line and move on.
   2. `$H verify <id> --phase before`. It runs the `$ ` checks (placeholders `{test_cmd}` `{lint_cmd}` `{build_cmd}` resolve to this project's commands). Also do every non-`$` check it lists under `manual` and say what you found. Fails: `$H finish <id> --status deferred --reason "baseline: <first failure>"` (it is retried next time; after 3 deferrals it is closed as failed).
   3. Make the change, touching only the declared paths (with auto-route: one `route-edit` worker, one writer per path). If the item's tests describe a new test, add it to the project's test framework (or a small scripted smoke test when there is none) and include that file in `--paths`.
   4. `$H verify <id> --phase after`: checks again, then the tests, plus built-in checks (no undeclared file changed, no duplicate sections, at least one test ran and passed). Do the `manual` items again.
   5. Anything failed: `$H rollback <id>` then `$H finish <id> --status failed --reason "<first failing line>"`.
   6. Passed, git repo: `$H commit <id>` (commits only the declared paths; the owner's other changes stay as they were). Commit refused: rollback, finish failed. Global item: no commit; the journal snapshot is the backup.
   7. `$H finish <id> --status applied --reason "<one line>"`.
   8. Push only if this repo's own AGENTS.md or workflow already pushes every change.
5. Tell the owner one line per item: `<id> applied (<sha>) | declined: reason | deferred/failed: reason`.

## Never, even with a YES
Force-push or rewrite history; delete the owner's data or files beyond the declared paths; add paid services, accounts, or API keys; send email, posts, or messages; change trust settings, `config.toml`, or other rules and hooks. Those need the owner in this session.

## Cost
Quick councils run in one pass with no sub-agents. Skip the whole flow in headless or scripted runs and when the owner's request is urgent; it waits for the next interactive session.
