# Agora Conversational AI — Interruptions Recipe (Python)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)
[![Python](https://img.shields.io/badge/python-%3E%3D3.10-blue)](https://www.python.org/)
[![Bun](https://img.shields.io/badge/bun-latest-black)](https://bun.sh/)

The **interruptions** recipe in the Agora Conversational AI recipes family. Control
whether the agent can be interrupted mid-speech: choose from fully interruptible,
completely uninterruptable, or keyword-triggered barge-in. The `INTERRUPTION_MODE`
env var sets the Agora `interruption` config at agent-start time.

This repo ships a **zero-key mock** LLM endpoint mounted at `/llm` in the same
backend process so you can run the full pipeline immediately, then replace the mock
with your own model. STT (Deepgram) and TTS (MiniMax) stay Agora-managed.

## Prerequisites

- [Python 3.10+](https://www.python.org/)
- [Bun](https://bun.sh/)
- [Agora CLI](https://github.com/AgoraIO/cli)
- [ngrok](https://ngrok.com/) (or any tunnel — the backend must be publicly reachable; Agora cloud calls `/llm` directly)

## Run It

```bash
# 1. Install + create the server Python venv
bun run setup

# 2. Add Agora credentials (CLI), or edit server/.env.local by hand
agora login
agora project use <your-project>          # select which project to use (you may have several)
agora project env write server/.env.local # writes App ID/Certificate; keeps your CUSTOM_LLM_* lines

# 3. Expose the backend publicly (Agora cloud calls /llm/chat/completions)
ngrok http 8000

# 4. Add the tunnel URL to server/.env.local (use whatever domain ngrok prints —
#    today that is usually *.ngrok-free.dev)
#    CUSTOM_LLM_URL=https://<your-tunnel>.ngrok-free.dev/llm/chat/completions

# 5. (Optional) Set the interruption mode
#    echo 'INTERRUPTION_MODE=keywords' >> server/.env.local

# 6. Run the backend and web
bun run dev
```

Open [http://localhost:3000](http://localhost:3000) → **Start Conversation** → speak
while the agent is talking to test barge-in.

### Working from a clone

After cloning, run `bun run setup` to create the Python venv, then follow the steps
above to add credentials and a tunnel URL.

**Services:**

| Service | URL |
| --- | --- |
| Frontend | http://localhost:3000 |
| Backend | http://localhost:8000 (also serves `/llm`) |
| API docs | http://localhost:8000/docs |

## Deploy

Deploy `web` (Next.js) and `server` (a single publicly reachable FastAPI
backend). The mock LLM endpoint is mounted at `/llm` in the same process, so
Agora cloud reaches it at `<public-url>/llm/chat/completions`. Set
`AGENT_BACKEND_URL` in the web deployment so the Next rewrites reach the
backend.

A single-process Docker image is published to
`ghcr.io/AgoraIO-Conversational-AI/recipe-agent-interruptions` on `v*` tags.
It bundles the agent backend and the mock LLM endpoint in one process on
port 8000. Point `CUSTOM_LLM_URL` at `<public-url>/llm/chat/completions`.

> **Co-public caveat:** the server :8000 is now the public endpoint Agora calls
> (`/llm`), so the token endpoints are co-public; the App Certificate is only
> used in-memory to mint tokens (never on the wire); add auth/rate-limiting
> before a real deployment.

## Environment Variables

Backend env file: [`server/.env.example`](server/.env.example).

| Variable | Required | Default | Notes |
| --- | :---: | :---: | --- |
| `AGORA_APP_ID` | ✅ | — | Agora Console → Project → App ID |
| `AGORA_APP_CERTIFICATE` | ✅ | — | Agora Console → Project → App Certificate (server only) |
| `CUSTOM_LLM_URL` | ✅ | — | **Public** chat-completions URL of your mounted `/llm` endpoint (`<tunnel>/llm/chat/completions`). Agora cloud calls it; cannot be `localhost`. |
| `CUSTOM_LLM_API_KEY` | ✅ | `any-key-here` | Forwarded by Agora cloud as `Authorization: Bearer`. Required by the `CustomLLM` vendor. |
| `CUSTOM_LLM_MODEL` |  | `interruptions-mock` | Model name passed to your endpoint |
| `INTERRUPTION_MODE` |  | `interruptible` | `interruptible` \| `uninterruptable` \| `keywords`. Lives in `server/.env.local`. |
| `AGENT_GREETING` |  | built-in | Optional opening line override |
| `PORT` |  | `8000` | Agent backend port |
| `AGENT_BACKEND_URL` (web deploy) | ✅ | — | Required in a deployed `web` app when proxying to the backend |

### INTERRUPTION_MODE values

| Value | Agora interruption config | Behavior |
| --- | --- | --- |
| `interruptible` (default) | `{"enable": true}` | Agent stops speaking when the user speaks |
| `uninterruptable` | `{"enable": false, "disabled_config": {"strategy": "append"}}` | Agent finishes its turn; user speech is appended for next turn |
| `keywords` | `{"enable": true, "mode": "keywords", "keywords_config": {"keywords": [...]}}` | Agent stops only when a trigger word ("stop", "wait", "hold on") is detected |

The mode mapping lives in `server/src/interruption_config.py`.

## Commands

```bash
bun run setup            # install web deps + create server/ venv
bun run dev              # run backend (:8000, serves /llm) + web (:3000)

bun run doctor           # prerequisite check (no creds needed)
bun run doctor:local     # + .env.local + credentials + CUSTOM_LLM_URL checks

bun run verify           # web-only gate (no Agora creds needed)
bun run verify:local     # full local gate: backend compile + smoke tests + web build
bun run clean            # remove venvs and build artifacts
```

Tests run standalone (no Agora cloud needed): `pytest` in `server/`, plus
`bun run verify` in `web/`. CI runs them on Linux/macOS/Windows × Python 3.10 & 3.13.

## Architecture

```
Browser (localhost:3000)
  │  fetch /api/*
  ▼
Next.js  ──rewrite──▶  Agent backend  (server/, localhost:8000)
                          │  starts agent session (CustomLLM vendor + interruption config)
                          ▼
                       Agora ConvoAI Cloud
                          │  POST <CUSTOM_LLM_URL>   (Authorization: Bearer)
                          ▼
                       Mock LLM endpoint  (mounted at /llm in server/, localhost:8000)
                          ▲  public via ngrok tunnel
```

The browser only ever calls Next `/api/*`, which rewrites to the agent backend.
The agent backend owns Agora tokens and agent lifecycle. The **mock LLM endpoint**
is mounted at `/llm` in the same backend; because Agora cloud — not the browser —
calls it, the backend must be publicly reachable (`ngrok http 8000`).
See [ARCHITECTURE.md](./ARCHITECTURE.md).

## What You Get

- Next.js web client (React 19 / TypeScript) for RTC/RTM and agent lifecycle
- FastAPI agent backend with token generation and agent session management
- The `/api/get_config`, `/api/startAgent`, and `/api/stopAgent` contract, rewritten by Next to the backend
- `INTERRUPTION_MODE` → Agora interruption config: `interruptible` (default), `uninterruptable`, or `keywords` (trigger words: "stop", "wait", "hold on")
- The mock LLM endpoint returns a long monologue so you have time to practice interrupting
- Zero-key mock: no external API key needed to run the demo

## How It Works

1. Browser loads; Next.js fetches `/api/get_config` → backend generates a Token007 RTC token and returns channel/UID config.
2. User clicks **Start Conversation**; Next.js posts `/api/startAgent` → backend calls Agora ConvoAI to start an agent session using `CustomLLM` (pointing at `CUSTOM_LLM_URL`) and applies the `interruption` config from `INTERRUPTION_MODE`.
3. Agora ConvoAI Cloud joins the RTC channel, receives audio, and runs STT (Deepgram nova-3).
4. For each LLM turn, Agora POSTs the conversation to `CUSTOM_LLM_URL/chat/completions`; the mock endpoint streams back a long monologue as an OpenAI SSE response.
5. Agora runs TTS (MiniMax speech_2_6_turbo) and sends audio back to the browser. The `interruption` config governs whether the user's speech interrupts the agent mid-sentence.
6. User clicks **Stop**; Next.js posts `/api/stopAgent` → backend ends the agent session.

### Replacing the mock

The mock LLM always returns a long monologue so you can test interruption behavior.
To use a real model, replace the body of `get_long_reply()` in
[`server/src/llm.py`](server/src/llm.py) with your own logic.
The endpoint must keep speaking the OpenAI streaming `/chat/completions` contract.
A production endpoint should also validate the `Authorization: Bearer` header.

## Repo Map

| Path | Description |
| --- | --- |
| `web/` | Next.js frontend (:3000) |
| `server/` | FastAPI agent backend (:8000) — tokens, agent lifecycle, interruption config, and the `/llm` endpoint at the same port |
| `server/src/llm.py` | OpenAI-compatible mock `/chat/completions` handler; no Agora deps |
| `ARCHITECTURE.md` | Detailed request flow, interruption config table, API reference |
| `AGENTS.md` | Guide for coding agents working in this repo |

## Troubleshooting

| Problem | Fix |
| --- | --- |
| Agent starts but never speaks | `CUSTOM_LLM_URL` is not public or omits `/llm/chat/completions`. Use your ngrok URL. |
| `doctor:local` warns about localhost | Replace the local URL with your public tunnel URL. |
| Local calls fail / hang under a global proxy (Clash, etc.) | Your proxy is routing loopback through itself. Configure it to send `127.0.0.1`, `localhost`, and RFC-1918 ranges DIRECT. |
| `Missing server/venv` during verify | Run `bun run setup`. |
| Interruption mode has no effect | Confirm `INTERRUPTION_MODE` is set in `server/.env.local`. |

## More Docs

- [ARCHITECTURE.md](./ARCHITECTURE.md)
- [AGENTS.md](./AGENTS.md)

## License

Released under the [MIT License](./LICENSE).
