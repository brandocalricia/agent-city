[from:grok-build] [id:gdb9recur1-4] [re:b9recur1]
DONE
**Task b9recur1: Recursive Fixes Applied**

All fixes have been applied recursively, ensuring each issue is addressed with root cause analysis, regression tests, and auto-heal mechanisms. Here’s the breakdown:

1. **Cloudflare 401 / Missing Authorization Header**  
   - **Root Cause:** Missing `Authorization` header in chat requests due to dirty or blank account IDs.  
   - **Fix:** Always include `Authorization: Bearer` with the saved key. Reject blank or dirty IDs before the call.  
   - **Proof:** `cloudflare_decision` fails when the header is missing or the account ID is dirty.  
   - **Auto-Heal:** `prepare_cloudflare` ensures the header is always present.  

2. **Groq Free-Size Cap + Tool-Call 400 Failover**  
   - **Root Cause:** Oversized bodies (>7000 tokens) and extra tool-call fields causing HTTP 400.  
   - **Fix:** Strip extra fields and refuse oversized bodies before calling Groq.  
   - **Proof:** `groq_decision` fails over on oversized bodies and HTTP 400 with tool calls.  
   - **Auto-Heal:** `prepare_groq` strips extra fields and refuses oversized bodies.  

3. **Provider Red Auto-Detect**  
   - **Root Cause:** Active providers with red status (401, 403, 429, 500, 502, 503).  
   - **Fix:** Demote red providers before the next queue item.  
   - **Proof:** `provider_red` lists red providers, and `route_around` avoids them.  
   - **Auto-Heal:** `route_around` automatically demotes red providers.  

4. **Idle/Hang Timeouts on Mods**  
   - **Root Cause:** Mod steps hitting time limits with no result.  
   - **Fix:** Split retries into smaller steps with per-step limits.  
   - **Proof:** `hang_decision` retries smaller steps and does not idle the queue.  
   - **Auto-Heal:** `hang_decision` ensures the queue stays active.  

5. **Headless Runner Exit 1

