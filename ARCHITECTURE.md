# Architecture — Interruptions Recipe

Two processes. The browser talks only to Next.js `/api/*`, which rewrites to the
agent backend. The agent backend owns Agora tokens and agent lifecycle, applies the
`INTERRUPTION_MODE` config when it starts the agent, and also serves the mock LLM
endpoint mounted at `/llm`, which **Agora cloud** calls directly.

## Request flow

```
Browser
  │  GET /api/get_config            → token + channel/UIDs
  │  POST /api/startAgent           → start agent session (with interruption config)
  ▼
Next.js  (rewrites /api/* → AGENT_BACKEND_URL)
  ▼
Agent backend (server/, :8000)
  │  builds session with CustomLLM(base_url=CUSTOM_LLM_URL)
  │  applies interruption config from INTERRUPTION_MODE
  ▼
Agora ConvoAI Cloud
  │  user speech → Deepgram STT (managed, nova-3)
  │  POST <CUSTOM_LLM_URL>/chat/completions   (Authorization: Bearer <key>)
  ▼
Mock LLM endpoint (mounted at /llm in server/, :8000, public via tunnel)
  │  returns long-monologue OpenAI SSE stream
  ▼
Agora ConvoAI Cloud → MiniMax TTS (managed, speech_2_6_turbo) → user hears speech
                     → RTM transcript / metrics → web UI
```

`POST /api/stopAgent { agentId }` ends the session.

## One process, two concerns

`server/` runs a single process that serves both the token/agent endpoints and,
mounted at `/llm`, the OpenAI-compatible mock LLM endpoint (`server/src/llm.py`).

The two concerns are kept in separate files with a one-directional dependency
(`server.py` imports `llm`, never the reverse), and `llm.py` has no `agora_agent`
import — it is the provider-agnostic part you replace with your own model.

Merging them onto one public surface is a deliberate trade. The Agora App
Certificate is only ever used in-memory to mint tokens — it never crosses a wire —
so co-locating the public `/llm` route with the token endpoints does not expose
the certificate. It does, however, make the token-minting endpoints
(`/get_config`, `/startAgent`, `/stopAgent`) publicly reachable. They are
unauthenticated in this recipe; put auth / rate-limiting in front of them
(ingress, gateway, or a proxy) before any real deployment.

## Interruption config

`server/src/interruption_config.py` maps `INTERRUPTION_MODE` to the Agora
`interruption` dict. The module has no `agora_agent` import so it is
unit-testable in isolation. Tests live in `server/tests/test_interruption_config.py`.

| Mode | Agora config |
| --- | --- |
| `interruptible` (default) | `{"enable": true}` |
| `uninterruptable` | `{"enable": false, "disabled_config": {"strategy": "append"}}` |
| `keywords` | `{"enable": true, "mode": "keywords", "keywords_config": {"keywords": [...]}}` |

## API (agent backend, port 8000)

| Endpoint | Method | Description |
| --- | --- | --- |
| `/get_config` | GET | Token + channel/UID config |
| `/startAgent` | POST | Start the agent session with interruption config |
| `/stopAgent` | POST | Stop the agent by `agent_id` |
| `/llm/chat/completions` | POST | OpenAI-compatible completions (monologue mock) |
| `/llm/health` | GET | LLM endpoint health check |

The browser calls the first three as `/api/*`; Next rewrites them to
`AGENT_BACKEND_URL`. Agora cloud calls `/llm/chat/completions` directly.

## Auth

- Browser → agent backend: none (local dev).
- Agent backend → Agora cloud: Token007, generated from `AGORA_APP_ID` +
  `AGORA_APP_CERTIFICATE`.
- Agora cloud → mock LLM endpoint: `Authorization: Bearer <CUSTOM_LLM_API_KEY>`.
  The mock endpoint does not validate it; a production endpoint should.
