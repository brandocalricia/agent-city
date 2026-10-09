# Swarm plan

Facts measured on OmniRoute 3.8.51. The quota table had 0 rows, so daily and per-minute caps stay **unknown**. Do not aim at 95% of a number that was not published. A 429 hops to the next free model. Grok stays the main session and the paced last resort.

## Pools

### NVIDIA NIM
- **State:** up. `moonshotai/kimi-k3` replied pong in 1172 ms.
- **Free models:** 11 chat models. `deepseek-v4-flash-0731` returned 410. `glm-5.3` and `kimi-k2.6` are not in this catalog. `nemotron-3-ultra-550b-a55b` is listed and was not chat-tested.
- **Priority:** 2

### Kilo Gateway
- **State:** up. No credential. Paid auto routes (`frontier`, `balanced`) are excluded.
- **Checked model:** `kilo-auto/free` returned HTTP 200 in 10946 ms. The visible reply was empty.
- **Priority:** 4

### OVHcloud
- **State:** up. Anonymous. `Mistral-Small-3.2-24B-Instruct-2506` replied pong in 838 ms. Llama 3.3 70B returned 429. `Qwen3.6-27B` is not in the live catalog. gpt-oss ids stay excluded.
- **Priority:** 5

### OpenRouter
- **State:** up. 14 free chat models. `cohere/north-mini-code:free` replied pong in 6679 ms. `google/gemma-4-31b-it:free` returned 429. The free router id returned HTTP 200 with an empty visible reply.
- **Priority:** 6

### DuckDuckGo
- **State:** up. Keyless. `mistral-small-2603` replied pong in 1883 ms, and again after a reload. gpt-oss is excluded. Do not send private text on this lane.
- **Priority:** 7

### llama.cpp local
- **State:** optional. Already running `Qwen3.5-4B-Q4_K_M` at context 16384. It was not restarted. The Mac has 24 GB installed, and free pages were about 150 MB while that process was resident, so a larger context was not loaded. A harness turn of about 17909 does not fit 16384. Draft only.
- **Priority:** 8

### Cerebras
- **State:** inactive. Two chat calls to `qwen-3.8-27b` returned 403. A direct call returned Cloudflare error 1010. No card was added.
- **Priority:** 80

### Not added
- Cloudflare Playground (`kimi-k2.6`): HTTP 502, browser executable missing.
- UncloseAI (`Qwen3.6-27B`): HTTP 404, model not on the upstream.
- OpenCode Free and AI Horde: still inactive. OpenCode does not answer outside OpenCode. AI Horde's listed models are image models.

### Waiting on an owner credential
Gemini, Groq, Mistral, Cloudflare, Z.ai, Longcat, Cohere, and LLM7. No signup was done from here.

### Grok
Main session, planning, and final review. Subagent reads, research, and tests are pinned to `auto/offline`. Code edits are pinned to `auto/coding`. High-stakes review stays on Grok. Compression stays stacked (rtk, then caveman). No SuperGrok OAuth in OmniRoute.

## Activity

Checked every 3 minutes. Full when at least 2 of Cerebras, NVIDIA, Kilo, OVH, OpenRouter, and DuckDuckGo are active and not in cooldown (workers = that count, max 3). Shifted when exactly one (workers = 1). Minimal when none (workers = 0). The first check after a cooldown time puts the cap back up.

Right now: full, 5/6 up, 3 workers, next reset none. Cerebras is the one down.

## Free share

| | Remote lanes | What was measured |
| --- | --- | --- |
| Before | 3 | One saved turn, 100% on the free side (17947 in, 74 out) |
| After | 5 | Four one-line checks replied pong on free lanes. Zero of those checks went to Grok |

`routed_free` stays 20817. That counter was not increased by these checks.

## Routing

Code uses `auto/coding`. Drafts use `auto/offline`. Order: NVIDIA, Kilo, OVH, OpenRouter, DuckDuckGo, then the local model. A failed answer retries once on a stronger free model, then paced Grok.

`tools/swarm_scheduler.py` prints this plan. It does not call a model and does not start processes.
