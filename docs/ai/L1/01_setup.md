# 01 · Setup

> Install dependencies, configure env, and run the interruptions recipe locally. This recipe is **zero-key** for the mock LLM but requires a public tunnel (`ngrok`) so Agora cloud can reach `/llm/chat/completions`.

## Prerequisites

- Python 3.10+ (backend runs on 3.10 and 3.13 in CI)
- [Bun](https://bun.sh/) (runs the web app and orchestration scripts)
- [Agora CLI](https://github.com/AgoraIO/cli) (optional; easiest way to mint App ID + Certificate)
- [ngrok](https://ngrok.com/) (or any tunnel — the backend must be publicly reachable; Agora cloud calls `/llm` directly)

## Install

```bash
bun run setup            # installs web deps + creates server/ venv from requirements.txt
```

`setup` runs `setup:env` (copies `server/.env.example` → `server/.env.local` if missing), `setup:server` (recreates `server/venv`, installs `requirements.txt`), and `setup:web` (`bun install`).

## Configure env

Backend env file is `server/.env.local` (template: `server/.env.example`).

| Variable                | Required | Default              | Notes                                                                                 |
| ----------------------- | :------: | -------------------- | ------------------------------------------------------------------------------------- |
| `AGORA_APP_ID`          |    ✅    | —                    | Agora Console → Project → App ID                                                      |
| `AGORA_APP_CERTIFICATE` |    ✅    | —                    | Agora Console → Project → App Certificate                                             |
| `CUSTOM_LLM_URL`        |    ✅    | —                    | **Public** chat-completions URL (`<tunnel>/llm/chat/completions`). Agora cloud calls it; cannot be `localhost`. |
| `CUSTOM_LLM_API_KEY`    |    ✅    | `any-key-here`       | Forwarded by Agora cloud as `Authorization: Bearer`. Required by `CustomLLM` vendor.  |
| `CUSTOM_LLM_MODEL`      |          | `interruptions-mock` | Model name passed to the LLM endpoint                                                 |
| `INTERRUPTION_MODE`     |          | `interruptible`      | `interruptible` \| `uninterruptable` \| `keywords`                                    |
| `AGENT_GREETING`        |          | built-in line        | Optional opening utterance override                                                   |

Fill credentials via the Agora CLI or by hand:

```bash
agora login
agora project use <your-project>
agora project env write server/.env.local   # writes App ID + Certificate
# then add CUSTOM_LLM_URL and optionally INTERRUPTION_MODE
```

> Do **not** add `PORT` to `server/.env.example` — see [07_gotchas](07_gotchas.md).

## Expose the backend publicly

Agora cloud calls `CUSTOM_LLM_URL` (the `/llm` endpoint) directly; the URL must be publicly reachable:

```bash
ngrok http 8000
# Copy the printed URL, then:
echo 'CUSTOM_LLM_URL=https://<your-tunnel>.ngrok-free.dev/llm/chat/completions' >> server/.env.local
```

## Run

```bash
bun run dev              # backend (:8000, also serves /llm) + web (:3000) via concurrently
```

Open <http://localhost:3000> → **Start Conversation** → speak while the agent is talking to test barge-in. Backend API docs at <http://localhost:8000/docs>.

## Quick commands

```bash
bun run doctor           # shared prereqs (bun + node_modules); no creds needed
bun run doctor:local     # + .env.local + AGORA_APP_ID/CERTIFICATE + CUSTOM_LLM_URL checks
bun run verify           # web-only gate (doctor + api contracts + web build)
bun run verify:local     # full local gate: backend compile + fastapi smoke + LLM smoke + proxy + web build
bun run clean            # remove venvs and build artifacts
```

Backend unit tests run standalone (no cloud, no creds):

```bash
cd server && pytest tests -v
```

## Related Deep Dives

- None. For what each verify command asserts, see [05_workflows](05_workflows.md) and [06_interfaces](06_interfaces.md).
