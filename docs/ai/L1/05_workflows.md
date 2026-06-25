# 05 · Workflows

> Step-by-step guides for the common changes in this recipe. Each ends with the narrowest verify command to run.

## Change the interruption mode

1. Set `INTERRUPTION_MODE` in `server/.env.local` to `interruptible`, `uninterruptable`, or `keywords`.
2. Restart `bun run dev` — the mode is read at `Agent.__init__` time.
3. No code change required for the three built-in modes.
4. Verify: `cd server && pytest tests/test_interruption_config.py -v`.

## Add a new interruption mode

1. Add a new branch in `build_interruption_config()` (`server/src/interruption_config.py`).
2. Add a test in `server/tests/test_interruption_config.py`.
3. Document the new value in `server/.env.example` and the root `README.md`.
4. Verify: `cd server && pytest tests -v`.

## Replace the mock LLM with a real model

1. Edit `get_long_reply()` in `server/src/llm.py` — replace the monologue with your model logic.
2. Set `CUSTOM_LLM_URL` to the public URL of your endpoint (if not hosting it in-process).
3. Set `CUSTOM_LLM_API_KEY` to the bearer token your endpoint expects.
4. Keep `llm.py` free of `agora_agent` imports.
5. Verify: `bun run verify:local:llm` (exercises the mounted endpoint end-to-end).

## Add or change a browser-facing route

1. Add the FastAPI handler in `server/src/server.py` (return the `{ code, msg, data }` envelope).
2. Add the `/api/<name>` → `/<name>` mapping in `web/next.config.ts` `rewrites()`.
3. Add a client helper in `web/src/services/api.ts`.
4. Extend `web/scripts/verify-api-contracts.ts` with the new path + envelope assertions.
5. Verify: `bun run verify:web` (and `bun run verify:local:fastapi` if it should go through the real backend).

## Change the agent prompt / greeting / model

1. Greeting: set `AGENT_GREETING` (env) or edit the default in `server/src/agent.py`.
2. LLM model: set `CUSTOM_LLM_MODEL` (default `interruptions-mock`).
3. Other vendor options (STT model, TTS voice): edit `Agent.start()` in `server/src/agent.py`.
4. Verify: `bun run verify:backend` (compile) + `cd server && pytest tests -v`.

## Adjust VAD / turn detection

1. Edit the `turn_detection` dict in `AgoraAgent(...)` inside `Agent.start()` (`server/src/agent.py`).
   Fields: `speech_threshold`, `start_of_speech.vad_config.interrupt_duration_ms`, `start_of_speech.vad_config.prefix_padding_ms`, `end_of_speech.vad_config.silence_duration_ms`.
2. See [interruption_config](L2/interruption_config.md) for the full shape.
3. Verify: `bun run verify:backend`.

## Run / debug locally

```bash
bun run dev              # both processes; open http://localhost:3000
bun run doctor:local     # check creds + .env.local + CUSTOM_LLM_URL before a live call
```

## Verify before finishing

| Change touches…              | Run                                                                              |
| ---------------------------- | -------------------------------------------------------------------------------- |
| Web only                     | `bun run verify:web`                                                              |
| Interruption config / agent  | `bun run verify:backend` + `cd server && pytest tests -v`                         |
| Mock LLM endpoint            | `bun run verify:local:llm`                                                        |
| Route/proxy boundary         | `bun run verify:web:proxy` and/or `bun run verify:local:fastapi`                 |
| Anything end-to-end (local)  | `bun run verify:local`                                                            |

## Deploy

1. Deploy `web/` as a Next.js app.
2. Deploy `server/` as a publicly reachable FastAPI service (the published single-process image is `ghcr.io/AgoraIO-Conversational-AI/recipe-agent-interruptions` on `v*` tags).
3. Set `AGENT_BACKEND_URL` in the web deployment so rewrites reach the backend.
4. Set `CUSTOM_LLM_URL` to `<public-backend-url>/llm/chat/completions`.

## Related Deep Dives

- [interruption_config](L2/interruption_config.md) — interruption mode config and VAD tuning details.
- [mock_llm_endpoint](L2/mock_llm_endpoint.md) — mock LLM contract and replacement guide.
