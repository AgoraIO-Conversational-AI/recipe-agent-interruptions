# 02 · Architecture

> Two co-located processes in one port. The browser talks only to Next.js `/api/*`, which rewrites to the FastAPI agent backend. The backend owns Agora tokens and the agent session, applies the `INTERRUPTION_MODE` config, and also serves the mock LLM endpoint that Agora cloud calls directly.

## Topology

```
Browser (localhost:3000)
  │  fetch /api/*
  ▼
Next.js (web/)  ──rewrite──▶  Agent backend (server/, :8000)
                                 │  starts agent session: CustomLLM vendor + interruption config
                                 │  mounts mock LLM at /llm (same process, same port)
                                 ▼
                              Agora ConvoAI Cloud
                                 │  user speech → Deepgram STT (managed, nova-3)
                                 │  POST <CUSTOM_LLM_URL>/chat/completions  (Bearer token)
                                 ▼
                              Mock LLM endpoint (/llm in server/, public via tunnel)
                                 │  streams long-monologue SSE
                                 ▼
                              Agora ConvoAI Cloud → MiniMax TTS (speech_2_6_turbo) → user hears speech
                                                  → RTM transcript + metrics → web UI
```

- **`web/`** — Next.js 16 / React 19 / TypeScript. Owns UI plus the RTC/RTM client lifecycle. Calls only `/api/*`.
- **`server/`** — Python FastAPI (:8000). Owns Agora token generation and agent session lifecycle. SDK: `agora-agents>=2.3.0` (`import agora_agent`).
- **`server/src/llm.py`** — provider-agnostic mock LLM; mounted at `/llm` in the same process. No `agora-agents` import. Agora cloud — not the browser — calls it.

## Request lifecycle

1. Browser `GET /api/get_config` → Next rewrites to backend `/get_config`; backend mints a Token007 from `AGORA_APP_ID` + `AGORA_APP_CERTIFICATE` and returns channel + UIDs.
2. Browser joins the RTC channel, then `POST /api/startAgent`; backend builds the STT/LLM/TTS vendor chain, applies the `interruption` dict from `build_interruption_config(INTERRUPTION_MODE)`, and starts an async agent session.
3. Agora runs STT (Deepgram nova-3), then POSTs each LLM turn to `CUSTOM_LLM_URL/chat/completions`; the mock endpoint streams back a long monologue as OpenAI SSE.
4. Agora runs TTS (MiniMax speech_2_6_turbo) and sends audio back. The `interruption` config governs barge-in behavior.
5. RTM delivers transcript + metrics to the web UI.
6. `POST /api/stopAgent { agentId }` ends the session.

## One process, two concerns

`server/` runs a single FastAPI process that serves both the token/agent endpoints and, mounted at `/llm`, the OpenAI-compatible mock LLM. The two concerns are in separate files with a one-directional dependency (`server.py` imports `llm`, never the reverse), and `llm.py` has no `agora_agent` import. This is the component a developer replaces.

Consequence: the `/llm` route and the token endpoints share a port and a public surface. The App Certificate never crosses a wire (it is used only to mint tokens in-memory), but `/get_config`, `/startAgent`, and `/stopAgent` are co-public. See [08_security](08_security.md).

## Key abstractions

- **`Agent`** (`server/src/agent.py`) — async wrapper around `AgoraAgent`; owns the `AsyncAgora` client, env, and the in-memory `_sessions` map keyed by `agent_id`.
- **`build_interruption_config()`** (`server/src/interruption_config.py`) — maps `INTERRUPTION_MODE` string to the Agora `interruption` dict. No `agora_agent` import; independently unit-testable.
- **Mock LLM** (`server/src/llm.py`) — FastAPI app mounted at `/llm`; `POST /chat/completions` always returns a long monologue so barge-in is testable without any API key.
- **Rewrite proxy** (`web/next.config.ts`) — the only browser→backend boundary; no Next Route Handlers for agent/token logic.

## Tech decisions

- **Rewrites, not Route Handlers** — hides backend placement behind `/api/*` so the same client works locally and deployed (set `AGENT_BACKEND_URL`).
- **Interruption config isolated** — `interruption_config.py` carries no SDK import so it can be tested without `agora-agents`.
- **No localhost default for `CUSTOM_LLM_URL`** — a localhost URL would let the agent start while LLM calls silently fail cloud-side.
- **Cascading vendors** — STT/LLM/TTS are separate Agora-managed vendors, unlike the realtime MLLM recipe. Turn detection is configured on `AgoraAgent(turn_detection={...})` using VAD.

## Related Deep Dives

- [interruption_config](L2/interruption_config.md) — full interruption mode mapping, VAD tuning, and keywords config.
- [mock_llm_endpoint](L2/mock_llm_endpoint.md) — mock LLM contract, SSE format, and replacement guide.
