---
name: city-council
description: >-
  Agent City's council, tailored for Grok Build. Use when the owner says
  "convene the council", "let the council decide", or /city-council, and as the
  YES/NO gate in city-apply. Full Council (14 seats + King + Red Team) for every
  city decision. No Quick Council shortcut. Reads IDEALS.md.
argument-hint: "<decision as a yes/no question>"
metadata:
  author: Agent City
  short-description: YES/NO council for code decisions
---
# City Council (Grok Build)

Based on the owner's `council` skill (roster, rubric, king protocol), cut down for a coding agent. Same 14 seats, same King and Red Team, same verdict format. Lean by default.

## 0. Read first
`~/.grok/agent-city/IDEALS.md` (or `IDEALS.md` in the agent-city repo). Every verdict says in one line how it fits the ideals and names any conflict.

## 1. Question Crystal (write it before any seat speaks)
- **Decision:** one yes/no sentence.
- **Repo and branch:** path, current branch, clean or dirty worktree (`git status --short`).
- **Files:** the paths the change would touch (read them; do not guess).
- **Tests:** the project's test command and whether it passes now. "No tests" is a fact, say it.
- **Checks and tests for this change:** the wiring checks (before and after) and the 1-2 tests that will prove it. No runnable test = NO for now.
- **Diff size:** rough lines added/removed.
- **Stakes, Reversibility, Constraints, Out of scope.**
Ask one clarifying question only if a field is unknown AND would change the answer. In city-apply, never ask: treat unknown as NO for now.

## 2. Size
Every city decision is **Full** (14 seats + King + Red Team). There is no Quick Council shortcut. The stakes below say why a decision is heavy. They do not open a shorter council:
- deletes or renames files, or deletes data the owner made
- changes a schema, public API, CLI flags, config format, or a migration
- force-push, history rewrite, branch delete, or anything touching a remote beyond a normal push
- adds a dependency, a paid service, a network call, or an MCP server
- security: secrets, auth, permissions, hooks, shell execution, trust settings
- raises recurring cost (tokens, model tier, API spend) or changes model routing
- edits global Grok config (`~/.grok/config.toml`, hooks) rather than one project
- conflicts with an ideal in IDEALS.md

## 3. Who runs where
Do not run a Quick Council for a city decision.
- **Full:** if sub-agents are available, spawn the seats in parallel as read-only workers on the cheap tier (with the owner's auto-route setup that is `route-read`, never pass a `model` argument, never use a fast premium variant). Give each worker the Crystal plus 3-4 seats to write independently (14 seats over 4 workers). One more read-only worker does the anonymous peer review (answers relabeled A-N). The King runs on the strongest tier: this session if it is on grok-4.7, else one `route-hard` worker. Red Team: one read-only worker that sees only the draft verdict. Depth limit is 1: workers never spawn. No sub-agents available: run everything in one pass here, and each seat still writes its own reason.

## 4. Seats (0-13)
0 Devil's Advocate, 1 Fresh Eyes, 2 Pessimist, 3 Optimist, 4 Pragmatist, 5 First-Principles (one back-of-envelope number), 6 Long-Term Strategist, 7 Domain Expert (state the field's consensus for this language/framework), 8 User Voice (the owner at his keyboard), 9 Risk Officer (worst case in concrete units: files lost, hours, dollars), 10 Resource Realist (tokens, time, what he is not doing instead), 11 Systems Thinker (one feedback loop), 12 Contrarian, 13 Historian (1-3 checkable prior cases).
Each answer, 40-80 words: Position, key reason, strongest objection to myself, what would change my mind. Code seats cite file paths or test output, not vibes.

## 5. Review, verdict, Red Team
- Peer review: one line per answer: six scores 1-10 (logic, evidence, feasibility, risk awareness, originality, steel-manning), total /60, fatal flaw or "none". Member i reviews (i+1), (i+5), (i+9) mod 14.
- King (wrote nothing, reviewed nothing): score audit, convergence (3+ seats), ignored angles (do-nothing, reversibility, cost), fatal-flaw check on the front-runner, then a verdict. No vote counting, no splitting the difference.
- Red Team: 3 one-line strikes on the draft; the King revises or rebuts each.

## 6. Verdict format
**YES** or **NO** first (decline to decide = NO for now), then: Recommendation (1-2 sentences); Confidence X/10; Ideals fit (one line); Load-bearing assumption; What would flip it; Dissent (named or "none"); Action: the exact next step (files, the checks, and the tests that must pass).

## 7. What a YES allows
A YES lets Grok Build make the change locally, pass its checks and tests, and commit (rolled back if any fail). It never allows, without the owner saying so in this session: force-push or history rewrite, deleting the owner's data or files outside the change, adding paid services or new accounts, sending or posting anything outside the machine. Push only if the repo's own AGENTS.md or workflow already pushes.

No emojis. No invented facts: name what is missing and reason in ranges.
