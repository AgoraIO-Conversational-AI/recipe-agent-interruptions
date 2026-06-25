# 08 · Security

> Trust boundaries, secret handling, co-public surface, and auth for the interruptions recipe.

## Trust boundaries

| Hop                              | Auth                                                                              |
| -------------------------------- | --------------------------------------------------------------------------------- |
| Browser → agent backend          | None in local dev (the `/api/*` rewrite is same-origin).                          |
| Agent backend → Agora cloud      | Token007, generated from `AGORA_APP_ID` + `AGORA_APP_CERTIFICATE`.                |
| Agora cloud → mock LLM endpoint  | `Authorization: Bearer <CUSTOM_LLM_API_KEY>`. The mock does not validate it; a production endpoint should. |

## Secret handling

- **Server-only secrets:** `AGORA_APP_CERTIFICATE` lives only in `server/.env.local` and never reaches the browser or crosses the wire. It is used only in-memory to mint Token007 tokens.
- `server/.env.local` is gitignored; `server/.env.example` ships placeholders only.
- Tokens (`generate_convo_ai_token`) expire after 3600s and are minted per `get_config` call for a concrete non-zero UID.
- `CUSTOM_LLM_API_KEY` is a bearer token sent by Agora cloud to the `/llm` endpoint; it is not a secret in the same sense as the App Certificate, but it should be rotated for production.

## Co-public surface

Because the mock LLM endpoint (`/llm`) and the token endpoints (`/get_config`, `/startAgent`, `/stopAgent`) share a single publicly reachable process, the token endpoints are co-public. The App Certificate is used only in-memory and never placed on the wire, so co-location does not expose it. However:

- `/get_config` generates and returns valid Agora tokens to any caller.
- `/startAgent` can start real Agora agent sessions.
- **Add auth and rate-limiting at the ingress/gateway layer before any real deployment.**

## CORS

The backend sets `CORSMiddleware` with `allow_origins=["*"]` — open by design for a local/dev recipe. **Lock this down to known origins before any production deployment.**

## Validation

- `Agent.__init__` raises `ValueError` for missing `AGORA_APP_ID`, `AGORA_APP_CERTIFICATE`, or `CUSTOM_LLM_URL`. The server sets `agent = None` and all routes return 500 until the env is corrected.
- `Agent.start()` rejects empty `channel_name` and non-positive `agent_uid`/`user_uid` before issuing tokens or starting a session.
- Route errors are sanitized: `_log_route_error` logs only non-`None` context; exceptions map to 400/500 without leaking internals to the client beyond the message.

## Deployment notes

- Set `AGENT_BACKEND_URL` only to a backend you control; the rewrite forwards browser requests there verbatim.
- The published Docker image is a single-process image (`:8000`); it does not bundle secrets and requires env vars at container start.
- The mock LLM does not validate the `Authorization: Bearer` header. Replace `get_long_reply()` and add header validation before production use.

## Related Deep Dives

- None.
