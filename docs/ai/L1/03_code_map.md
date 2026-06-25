# 03 · Code Map

> Where things live. Two top-level modules: `web/` (Next.js client) and `server/` (FastAPI backend + mock LLM). Orchestration is in the root `package.json`.

## Root

| Path                  | Responsibility                                                        |
| --------------------- | --------------------------------------------------------------------- |
| `package.json`        | Bun workspace; `setup`, `dev`, `doctor*`, `verify*`, `clean` scripts. |
| `README.md`           | Setup, run modes, env vars, interruption mode table, troubleshooting. |
| `ARCHITECTURE.md`     | System shape, request flow, interruption config table, API reference. |
| `AGENTS.md`           | Coding-agent handbook + How to Load / Git Conventions / Doc Commands. |
| `Dockerfile`          | Single-process image (`:8000`): agent backend + mock LLM.            |
| `.github/workflows/`  | `ci.yml` (backend pytest matrix + web verify), `docker.yml`, `nightly.yml`. |

## `server/` — FastAPI backend (:8000)

| Path                                    | Responsibility                                                                  |
| --------------------------------------- | ------------------------------------------------------------------------------- |
| `src/server.py`                         | FastAPI app, CORS, route handlers, error mapping, LLM mount, uvicorn entrypoint. |
| `src/agent.py`                          | `Agent` class: `AsyncAgora` client, `start()`/`stop()`, `_sessions`, vendor chain build. |
| `src/interruption_config.py`            | `build_interruption_config()` — maps `INTERRUPTION_MODE` to the Agora `interruption` dict. No `agora_agent` import. |
| `src/llm.py`                            | OpenAI-compatible mock `/chat/completions`; streams long-monologue SSE. No `agora-agents` dep. |
| `scripts/run_fake_server.py`            | Boots `server.app` with a `FakeAgent` for the local FastAPI smoke test.         |
| `tests/test_agent_construction.py`      | Builds the real `AgoraAgent`, fakes the SDK session, asserts shape.             |
| `tests/test_interruption_config.py`     | Asserts all three interruption modes + edge cases (case-insensitive, unknown).  |
| `tests/test_llm.py`                     | LLM endpoint in isolation: health, SSE contract, non-streaming rejected.        |
| `tests/test_llm_mount.py`               | LLM mounted under `/llm` in the server app; asserts no `agora_agent` import.   |
| `tests/conftest.py`                     | `fake_env` fixture + `FakeAgent` + `server_module`/`client` fixtures; no cloud, no real creds. |
| `.env.example`                          | Env template (do not add `PORT`).                                               |
| `requirements*.txt`                     | Runtime + dev (pytest) deps.                                                    |

## `server/src/server.py` routes

- `GET /get_config` — token + channel/UID config.
- `POST /startAgent` — start the agent session with interruption config.
- `POST /stopAgent` — stop by `agent_id`.
- `POST /llm/chat/completions` — mock LLM (via mount); Agora cloud calls this.
- `GET /llm/health` — LLM endpoint health check.

## `web/` — Next.js client (:3000)

| Path                                      | Responsibility                                                    |
| ----------------------------------------- | ----------------------------------------------------------------- |
| `next.config.ts`                          | `/api/*` rewrites to `AGENT_BACKEND_URL`; strict mode; Turbopack root. |
| `src/services/api.ts`                     | Browser API client: `getConfig`, `startAgent`, `stopAgent`.       |
| `src/lib/conversation.ts`                 | Transcript normalization, timestamp/UID mapping, visualizer state.|
| `src/lib/agora.ts`                        | Agora RTC/RTM helpers.                                            |
| `src/components/LandingPage.tsx`          | Conversation entry: config fetch, agent start, RTM login, teardown.|
| `src/components/ConversationComponent.tsx`| RTC join, mic publish, transcript/metrics/state listeners.        |
| `src/components/Quickstart*.tsx`          | Pre-call, transcript, metrics, layout panels.                     |
| `scripts/verify-api-contracts.ts`         | Asserts rewrites + client paths + response envelope (no network). |
| `scripts/verify-local-proxy.ts`           | Stub backend; proxies `/api/*` through the rewrite map.           |
| `scripts/verify-local-fastapi.ts`         | Spawns real FastAPI with `FakeAgent`; proxies routes end-to-end.  |
| `scripts/verify-local-llm.ts`             | Spawns real FastAPI + LLM mount; exercises `/llm/chat/completions`.|
| `scripts/doctor.ts`                       | Web prerequisite check.                                           |

## Related Deep Dives

- None. For runtime flow see [02_architecture](02_architecture.md); for contracts see [06_interfaces](06_interfaces.md).
