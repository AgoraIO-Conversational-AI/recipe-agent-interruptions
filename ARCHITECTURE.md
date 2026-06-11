# Architecture — Interruptions Recipe

Three processes. The browser talks only to Next.js `/api/*`, which rewrites to the
agent backend. The agent backend owns Agora tokens and agent lifecycle, and applies
the `INTERRUPTION_MODE` config when it starts the agent. The mock LLM endpoint is a
separate service that **Agora cloud** calls directly.

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
Mock LLM endpoint (llm/, :8001, public via tunnel)
  │  returns long-monologue OpenAI SSE stream
  ▼
Agora ConvoAI Cloud → MiniMax TTS (managed, speech_2_6_turbo) → user hears speech
                     → RTM transcript / metrics → web UI
```

`POST /api/stopAgent { agentId }` ends the session.

## Interruption config

`server/src/interruption_config.py` maps `INTERRUPTION_MODE` to the Agora
`interruption` dict. The module has no `agora_agent` import so it is
unit-testable in isolation. Tests live in `server/tests/test_interruption_config.py`.

| Mode | Agora config |
| --- | --- |
| `interruptible` (default) | `{"enable": true}` |
| `uninterruptable` | `{"enable": false, "disabled_config": {"strategy": "append"}}` |
| `keywords` | `{"enable": true, "mode": "keywords", "keywords_config": {"keywords": [...]}}` |

## Why two backends

`server/` and `llm/` are split because of an **exposure asymmetry**:

- `llm/` must be reachable by **Agora cloud over the public internet** (hence the
  ngrok tunnel). It is the part you replace with your own model, and it has no
  Agora dependency.
- `server/` only needs to be reachable by your web tier. It holds the Agora App
  Certificate and all token logic.

In production the two could be co-deployed, but they are kept separate here to
make that boundary — and the public-exposure requirement — explicit.

## API (agent backend, port 8000)

| Endpoint | Method | Description |
| --- | --- | --- |
| `/get_config` | GET | Token + channel/UID config |
| `/startAgent` | POST | Start the agent session with interruption config |
| `/stopAgent` | POST | Stop the agent by `agent_id` |

The browser calls these as `/api/*`; Next rewrites them to `AGENT_BACKEND_URL`.

## Auth

- Browser → agent backend: none (local dev).
- Agent backend → Agora cloud: Token007, generated from `AGORA_APP_ID` +
  `AGORA_APP_CERTIFICATE`.
- Agora cloud → mock LLM endpoint: `Authorization: Bearer <CUSTOM_LLM_API_KEY>`.
  The mock endpoint does not validate it; a production endpoint should.
