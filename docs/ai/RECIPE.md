---
recipe_version: 1.0.0
recipe_status: experimental
extension_points:
  - id: agent.interruption-mode
    name: INTERRUPTION_MODE env var (interruptible / uninterruptable / keywords)
  - id: agent.llm-endpoint
    name: CustomLLM vendor base_url, api_key, model, and mock logic in llm.py
  - id: api.routes
    name: Browser-facing API routes
  - id: web.conversation-ui
    name: Conversation UI panels and controls
  - id: verification.contracts
    name: Contract, proxy, local FastAPI, and LLM smoke verification
invariants:
  - id: api.rewrite-boundary
    summary: Browser calls stay on /api/* and Next rewrites to FastAPI; no Route Handlers for agent/token logic.
  - id: secrets.server-only
    summary: Agora App Certificate stays in the Python backend; CUSTOM_LLM_API_KEY is a bearer token forwarded by Agora cloud, not kept in the browser.
  - id: llm.agora-free
    summary: server/src/llm.py must not import agora_agent; it is a provider-agnostic component developers replace.
  - id: interruption.config-module
    summary: interruption_config.py has no agora_agent import and must remain independently unit-testable.
  - id: token.uid-concrete
    summary: Backend resolves missing, zero, or negative UIDs before issuing an RTC+RTM token.
  - id: llm.public-url
    summary: CUSTOM_LLM_URL must be a publicly reachable URL; there is no localhost default (Agora cloud calls it).
stable_contracts:
  - id: env.required
    summary: AGORA_APP_ID, AGORA_APP_CERTIFICATE, CUSTOM_LLM_URL, and CUSTOM_LLM_API_KEY are required.
  - id: api.core-routes
    summary: GET /api/get_config, POST /api/startAgent, and POST /api/stopAgent remain the browser-facing contract.
  - id: response.envelope
    summary: Successful backend responses use { code, msg, data }.
  - id: llm.mount
    summary: The mock LLM endpoint is mounted at /llm in the same process; Agora cloud reaches it at <public-url>/llm/chat/completions.
---

# Recipe Contract

This base recipe defines the reusable surface for a Python-backed Agora Conversational AI **interruptions** quickstart: a cascading STT/LLM/TTS pipeline with configurable barge-in behavior and a zero-key mock LLM co-hosted in the same process.

## Recipe Role

- Role: `base` recipe (self-contained, clone-and-run; no `Extends` pin).
- Target audience: developers who want to control whether a voice agent can be interrupted mid-speech, and want a zero-key demo they can run immediately before swapping in a real LLM.
- Reuse model: clone, bind project, expose the backend publicly (ngrok), set `CUSTOM_LLM_URL`, run, then customize interruption mode or replace the mock LLM.

## Recipe Scope

- Python FastAPI token generation and managed agent lifecycle.
- Cascading STT (`DeepgramSTT`, nova-3) + `CustomLLM` + TTS (`MiniMaxTTS`, speech_2_6_turbo) vendor chain.
- Agora `interruption` config applied at session start, driven by `INTERRUPTION_MODE`.
- Zero-key mock LLM (`server/src/llm.py`) mounted at `/llm` in the same process, returning a long monologue for barge-in testing.
- Next.js browser UI with RTC audio, RTM transcript/metrics, connection status.
- Rewrite-only `/api/*` browser facade hiding backend placement.
- Contract, proxy, local FastAPI, and LLM smoke verification that need no live Agora calls.

## Baseline Implementation Guidance

Use this repo's source and progressive disclosure docs as the starting point. Do not recreate the Agora ConvoAI integration or interruption config shape from memory — vendor schemas, SDK builder fields, token behavior, and RTM details drift. Copy verified patterns from this repo.

## Extension Points

| ID | Surface | How to extend | Required follow-up |
| -- | ------- | ------------- | ------------------ |
| `agent.interruption-mode` | `server/src/interruption_config.py`, `server/.env.local` | Add a new mode mapping in `build_interruption_config()` and document the new `INTERRUPTION_MODE` value. | Add a test in `test_interruption_config.py`; update `server/.env.example` and README. |
| `agent.llm-endpoint` | `server/src/llm.py`, `server/.env.local` | Replace `get_long_reply()` body with real model logic (Ollama, OpenAI, Anthropic, etc.); set `CUSTOM_LLM_URL` to the public URL. | Keep `/chat/completions` OpenAI-compatible SSE; keep `llm.py` free of `agora_agent` imports. |
| `api.routes` | `server/src/server.py`, `web/next.config.ts`, `web/src/services/api.ts` | Add FastAPI route, add rewrite, add browser fetch helper. | Extend `web/scripts/verify-api-contracts.ts`; add proxy/fastapi coverage if it belongs in local verification. |
| `web.conversation-ui` | `web/src/components/*`, `web/src/lib/conversation.ts` | Customize pre-call, transcript, metrics, connection status, mic, or visualizer UI. | Preserve RTC/RTM lifecycle ownership and transcript UID normalization. |
| `verification.contracts` | `web/scripts/*.ts`, root `package.json` | Add checks for new browser/backend boundaries. | Keep checks runnable without live Agora credentials. |

## Invariants

- Browser code calls only `/api/get_config`, `/api/startAgent`, and `/api/stopAgent` for the default flow.
- Next.js owns `/api/*` through rewrites only; no `web/app/api/**/route.ts` for agent/token logic.
- FastAPI owns token generation, `AGORA_APP_CERTIFICATE`, and agent lifecycle.
- `server/src/llm.py` has no `agora_agent` import; it is provider-agnostic.
- `interruption_config.py` has no `agora_agent` import; it is independently unit-testable.
- `CUSTOM_LLM_URL` must be publicly reachable; there is no localhost default.
- The backend issues one RTC+RTM-capable token for a concrete non-zero UID.

## Stable Contracts

| Contract | Stable shape |
| -------- | ------------ |
| Required backend env | `AGORA_APP_ID`, `AGORA_APP_CERTIFICATE`, `CUSTOM_LLM_URL`, `CUSTOM_LLM_API_KEY` |
| Optional backend env | `CUSTOM_LLM_MODEL`, `AGENT_GREETING`, `INTERRUPTION_MODE`, `PORT` (env only) |
| Required web deploy env | `AGENT_BACKEND_URL` |
| `GET /api/get_config` | Query `channel?`, `uid?`; returns `data.app_id`, `data.token`, `data.uid`, `data.channel_name`, `data.agent_uid`. |
| `POST /api/startAgent` | Body `{ channelName, rtcUid, userUid, parameters? }`; returns `data.agent_id`, `data.channel_name`, `data.status`. |
| `POST /api/stopAgent` | Body `{ agentId }`; returns `{ code: 0, msg: "success" }`. |
| `POST /llm/chat/completions` | OpenAI-compatible SSE streaming; called by Agora cloud with `Authorization: Bearer <CUSTOM_LLM_API_KEY>`. |
| Success envelope | `{ "code": 0, "msg": "success", "data": ... }` where the route has data. |
| Verification entry points | `bun run verify:web`, `bun run verify:backend`, `bun run verify:web:proxy`, `bun run verify:local:fastapi`, `bun run verify:local:llm`, `bun run verify:local`. |

## Internal / Subject to Change

- Visual layout, component composition, Tailwind classes, and assets under `web/src/components/`.
- Exact monologue text and streaming word-delay in `llm.py`.
- In-memory `Agent._sessions` details; the stable behavior is start by channel/user and stop by returned `agent_id`.
- Verification internals under `web/scripts/`; the stable surface is the root script names and what they assert.
- `agora-agents` SDK minor-version behavior; this recipe lower-bounds `>=2.3.0` but does not freeze every field.

## Related Progressive Disclosure Docs

- `L1/01_setup.md` — setup, env, and commands.
- `L1/02_architecture.md` — request flow and topology.
- `L1/05_workflows.md` — common modification workflows.
- `L1/06_interfaces.md` — route, rewrite, env, and interruption config contracts.
- `L1/L2/interruption_config.md` — full interruption mode config detail and VAD tuning.
- `L1/L2/mock_llm_endpoint.md` — mock LLM contract and replacement guide.
