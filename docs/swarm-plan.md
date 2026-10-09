# Swarm plan

Facts measured on OmniRoute 3.8.51. Remaining request quotas were not published by the providers, so they stay **unknown**. Three remote free chat providers answered. The worker cap is **full / 3**. No worker processes were started. Grok stays the main session and the paced last resort.

## Pools

### Cerebras
- **State:** up. Chat pass on `qwen-3.8-27b` at cost 0. `gpt-oss-120b` also answers; its cost estimate was non-zero, so it is out of the default pool. Two catalog ids returned 404 and are excluded.
- **Free models:** 2 live, 1 in the default pool.
- **Priority:** 1

### NVIDIA NIM
- **State:** up. Chat pass at cost 0.
- **Free models:** 11 chat models in the pool. 11 non-chat models excluded.
- **Priority:** 2

### OpenRouter
- **State:** up. A free chat model passed at cost 0. One other free model was cooling down.
- **Free models:** 14 in the pool. Paid catalog models are not in the pool.
- **Priority:** 3

### llama.cpp local
- **State:** optional. The process was already running, so it was not restarted. Chat HTTP 200. Context 16384. A harness turn of about 17909 does not fit. Draft only.
- **Priority:** 8

### OpenCode Free and AI Horde
- **State:** inactive. OpenCode's free chat does not answer outside OpenCode. AI Horde's listed models are image models. Both are out of the chat pools.

### Grok
- **State:** main session, and the review / planning roles. Last resort after one stronger free retry. No SuperGrok OAuth in OmniRoute.

## Activity

Checked every 3 minutes. Full when at least 2 of Cerebras, NVIDIA, and OpenRouter are active and not in cooldown (workers = that count, max 3). Shifted when exactly one (workers = 1). Minimal when none (workers = 0, channel watch only). The first check after a cooldown time puts the cap back up. Right now: full, 3, next reset none.

## Routing

Code uses `auto/coding` (quality-first: task fit 0.3524, health 0.1714, stability 0.1429). Drafts and bulk reads use `auto/offline` (offline-friendly: quota 0.3324, health 0.2667). A failed answer retries once on a stronger free model, then paced Grok. High-stakes review stays on Grok.

## Today

| Lane | Count |
| --- | --- |
| Remote free providers up | 3 |
| Local | 1, optional |
| Worker cap | 3 (none started) |
| Grok fallback | paced, last |

`tools/swarm_scheduler.py` prints this plan. It does not call a model and does not start processes.
