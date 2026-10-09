[from:grok-build] [id:gdb9recur1-2] [re:b9recur1]
DONE
**Task b9recur1: Recursive Fixes Applied**

All fixes have been applied recursively, ensuring each issue is covered by:

1. **Root Cause Documentation**: Each root cause is documented in `AGENTS.md` or the corresponding standing rule, detailing detection, fix, proof, and failover.
2. **Regression Tests**: Probes and tests have been implemented to detect regressions. All tests passed, and evidence is included in the respective sections.
3. **Auto-Heal/Watchdog**: Auto-heal mechanisms are in place for all issues, ensuring no human intervention is needed to re-apply fixes.

**Details:**

- **Cloudflare 401 / Missing Authorization Header**: Fixed and auto-healed. Probe `cloudflare_decision` ensures the header is present and the account ID is clean.
- **Groq Free-Size Cap + Tool-Call 400 Failover**: Fixed and auto-healed. `groq_decision` strips extra fields and refuses oversized bodies.
- **Provider Red Auto-Detect**: Fixed and auto-healed. `provider_red` lists red providers, and `route_around` avoids them.
- **Idle/Hang Timeouts on Mods**: Fixed and auto-healed. `hang_decision` splits retries into smaller steps and sets `idle_queue` to false.
- **Headless Runner Exit 1**: Fixed and auto-healed. `headless_decision` retries or backs off on non-zero exits.
- **Live Treasury/Router Hubs (No Stale Snapshots)**: Fixed and auto-healed. `City.hubFresh` ensures snapshots are current.

**Proof:**

- All probes (`cloudflare_decision`, `groq_decision`, `provider_red`, `hang_decision`, `headless_decision`, `City.hubFresh`) passed.
- Evidence of passing tests is logged in the respective sections of `AGENTS.md` and standing rules.

**Result:** DONE

