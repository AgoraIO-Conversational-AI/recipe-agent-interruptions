# 06 · Interfaces

> Boundary contracts: backend routes, the `/api/*` rewrite map, env vars, the response envelope, interruption config dict shapes, and the mock LLM endpoint.

## Backend routes (port 8000)

The browser calls the first three as `/api/<name>`; Next rewrites to the backend `/<name>`. Agora cloud calls `/llm/chat/completions` directly.

### `GET /get_config`

- Query (optional): `channel?: string`, `uid?: int` (≤ 0 or missing → backend generates one).
- Returns `data`: `{ app_id, token, uid (string), channel_name, agent_uid (string) }`.
- Token is a Token007 RTC+RTM token, expiry 3600s, for a concrete non-zero UID.

### `POST /startAgent`

- Body: `{ channelName: string, rtcUid: int, userUid: int, parameters?: object }`.
  - `parameters.output_audio_codec?: string` is the only honored parameter field.
- Returns `data`: `{ agent_id, channel_name, status: "started" }`.
- 400 if `channelName`/`rtcUid`/`userUid` are invalid or required env vars are missing.

### `POST /stopAgent`

- Body: `{ agentId: string }`.
- Returns `{ code: 0, msg: "success" }` (no `data`).

### `POST /llm/chat/completions`

- Called by Agora cloud (not the browser) with `Authorization: Bearer <CUSTOM_LLM_API_KEY>`.
- Body: OpenAI `ChatCompletionRequest` with `stream: true` (streaming required).
- Returns: `StreamingResponse` with `media_type="text/event-stream"` in OpenAI SSE chunk format.
- Final chunk: `"data: [DONE]\n\n"`.
- 400 if `stream: false`.

### `GET /llm/health`

- Returns `{ status: "ok", service: "interruptions-mock-llm" }`.

## Response envelope

```json
{ "code": 0, "msg": "success", "data": { } }
```

`data` omitted when the route has no payload. Non-zero `code` or missing `data` = error on the client side.

## Rewrite map (`web/next.config.ts`)

| Browser path        | Backend destination |
| ------------------- | ------------------- |
| `/api/get_config`   | `/get_config`       |
| `/api/startAgent`   | `/startAgent`       |
| `/api/stopAgent`    | `/stopAgent`        |

`rewrites()` returns `[]` when `AGENT_BACKEND_URL` is unset. The contract is asserted by `verify-api-contracts.ts` and exercised by `verify-local-proxy.ts`.

## Browser API client (`web/src/services/api.ts`)

- `getConfig({ channel?, uid? }) → GetConfigResponse`
- `startAgent(channelName, rtcUid, userUid) → agent_id`
- `stopAgent(agentId) → void`

## Environment variables

| Variable                | Scope          | Required | Default              |
| ----------------------- | -------------- | :------: | -------------------- |
| `AGORA_APP_ID`          | backend        |    ✅    | —                    |
| `AGORA_APP_CERTIFICATE` | backend        |    ✅    | —                    |
| `CUSTOM_LLM_URL`        | backend        |    ✅    | — (must be public)   |
| `CUSTOM_LLM_API_KEY`    | backend        |    ✅    | `any-key-here`       |
| `CUSTOM_LLM_MODEL`      | backend        |          | `interruptions-mock` |
| `INTERRUPTION_MODE`     | backend        |          | `interruptible`      |
| `AGENT_GREETING`        | backend        |          | built-in line        |
| `AGENT_BACKEND_URL`     | web (deploy)   |    ✅\*  | `http://localhost:8000` (dev) |
| `PORT`                  | backend (env only) |      | `8000` — do **not** put in `.env.example` |

\* Required wherever the web app is deployed; rewrites are empty without it.

## Interruption config (`server/src/interruption_config.py`)

`build_interruption_config(mode: str | None) → dict` — returns the Agora `interruption` dict:

| Mode | Returned dict |
| ---- | ------------- |
| `interruptible` (default) | `{"enable": True}` |
| `uninterruptable` | `{"enable": False, "disabled_config": {"strategy": "append"}}` |
| `keywords` | `{"enable": True, "mode": "keywords", "keywords_config": {"keywords": ["stop", "wait", "hold on"]}}` |
| any other / `None` | `{"enable": True}` (falls through to interruptible) |

Mode matching is case-insensitive and stripped.

## VAD / turn detection config (`server/src/agent.py`)

The `turn_detection` dict passed to `AgoraAgent(...)`:

```python
{
    "config": {
        "speech_threshold": 0.5,
        "start_of_speech": {
            "mode": "vad",
            "vad_config": {
                "interrupt_duration_ms": 160,
                "prefix_padding_ms": 300,
            },
        },
        "end_of_speech": {
            "mode": "vad",
            "vad_config": {
                "silence_duration_ms": 480,
            },
        },
    },
}
```

## Related Deep Dives

- [interruption_config](L2/interruption_config.md) — full interruption + VAD config details and tuning guide.
- [mock_llm_endpoint](L2/mock_llm_endpoint.md) — mock LLM SSE contract and replacement.
