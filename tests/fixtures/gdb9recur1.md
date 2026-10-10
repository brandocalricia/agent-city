[from:grok-build] [id:gdb9recur1] [re:b9recur1]
DONE
**Task b9recur1: Recursive Fixes Applied**

All fixes have been applied recursively, ensuring auto-heal and watchdog coverage. Regression tests and probes are in place for each issue. Here’s the summary:

1. **Cloudflare 401 / Missing Authorization Header**  
   - Root cause documented in `AGENTS.md`.  
   - Probe: `cloudflare_decision` fails if the header is missing or account ID is dirty.  
   - Auto-heal: Rejects invalid IDs before the call.  

2. **Groq Free-Size Cap + Tool-Call 400 Failover**  
   - Root cause documented in `AGENTS.md`.  
   - Probe: `groq_decision` fails over on oversized bodies or HTTP 400 with tool calls.  
   - Auto-heal: Strips extra fields and refuses oversized bodies.  

3. **Provider Red Auto-Detect**  
   - Root cause documented in `AGENTS.md`.  
   - Probe: `provider_red` lists red providers, and `route_around` avoids them.  
   - Auto-heal: `route_around` moves red providers behind healthy ones.  

4. **Idle/Hang Timeouts on Mods**  
   - Root cause documented in `AGENTS.md`.  
   - Probe: `hang_decision` ensures retries with smaller steps and switches lanes on second timeout.  
   - Auto-heal: `hang_decision` keeps the queue active.  

5. **Headless Runner Exit 1**  
   - Root cause documented in `AGENTS.md`.  
   - Probe: `headless_decision` retries or backs off on streaks.  
   - Auto-heal: `headless_decision` handles retries and streaks.  

6. **Live Treasury/Router Hubs (No Stale Snapshots)**  
   - Root cause documented in `AGENTS.md`.  
   - Probe: `City.hubFresh` ensures `measured_at` is current.  
   - Auto-heal: Page runs `City.hubFresh` on every open.  

**Proof:**  
All probes passed. Evidence:  
- `python3 tools/recur.py` output: `All checks passed. No regressions detected.`  

Task complete. Stopping as instructed.

