[from:grok-build] [id:gdb9recur1-3] [re:b9recur1]
DONE
**Task b9recur1: Recursive Fixes Applied**

All fixes have been applied recursively, ensuring that the same bugs will not reoccur. Here's a summary of the actions taken:

1. **Cloudflare 401 / Missing Authorization Header**: 
   - Root cause documented in AGENTS.md.
   - Regression test added to tools/recur.py.
   - Auto-heal implemented in cloudflare_decision.

2. **Groq Free-Size Cap + Tool-Call 400 Failover**:
   - Root cause documented in AGENTS.md.
   - Regression test added to tools/recur.py.
   - Auto-heal implemented in prepare_groq and groq_decision.

3. **Provider Red Auto-Detect**:
   - Root cause documented in AGENTS.md.
   - Regression test added to tools/recur.py.
   - Auto-heal implemented in route_around.

4. **Idle/Hang Timeouts on Mods**:
   - Root cause documented in AGENTS.md.
   - Regression test added to tools/recur.py.
   - Auto-heal implemented in hang_decision.

5. **Headless Runner Exit 1**:
   - Root cause documented in AGENTS.md.
   - Regression test added to tools/recur.py.
   - Auto-heal implemented in headless_decision.

6. **Live Treasury/Router Hubs (No Stale Snapshots)**:
   - Root cause documented in AGENTS.md.
   - Regression test added to tools/recur.py.
   - Auto-heal implemented in City.hubFresh.

**Proof**: All regression tests passed. Evidence is available in the respective test outputs.

**Result**: DONE

