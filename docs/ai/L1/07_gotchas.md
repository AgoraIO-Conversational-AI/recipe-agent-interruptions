# 07 · Gotchas

> Non-obvious pitfalls specific to the interruptions recipe. Read before changing the agent, env, LLM endpoint, or verify scripts.

## `CUSTOM_LLM_URL` must be public — no localhost default

`CUSTOM_LLM_URL` is the URL **Agora cloud** uses to call your LLM endpoint. Agora's cloud servers cannot reach `localhost` or `127.0.0.1`. Setting a local URL lets the agent "start" with a 200 OK, but every LLM turn silently fails cloud-side and the agent never speaks.

There is **no localhost default** by design. If `CUSTOM_LLM_URL` is unset, `Agent.__init__` raises `ValueError` immediately. Use `ngrok http 8000` (or any tunnel), then set `CUSTOM_LLM_URL=https://<tunnel>/llm/chat/completions`.

## Both `CUSTOM_LLM_URL` and `CUSTOM_LLM_API_KEY` are required

The `CustomLLM` vendor requires both `base_url` and `api_key`. If `CUSTOM_LLM_API_KEY` is empty, `Agent.__init__` raises `ValueError`. The default value `any-key-here` is sufficient for the mock; set it to a real secret for production.

## `CUSTOM_LLM_URL` must include the `/llm/chat/completions` path

The mock endpoint is mounted at `/llm` and exposes `POST /chat/completions`. The full path the URL must end with is `/llm/chat/completions`. Agora cloud does not append a path; it calls `CUSTOM_LLM_URL` verbatim.

## Do not put `PORT` in `server/.env.example`

`verify:local:fastapi` and `verify:local:llm` inject a random `PORT` and load env with `load_dotenv(override=True)`. A `PORT` line in `.env.example` (copied to `.env.local`) would clobber the injected port and break the smoke tests.

## `llm.py` must not import `agora_agent`

`test_llm_mount.py` AST-walks `llm.py` and fails if any `agora*` root is found on the import tree. Keep `llm.py` provider-agnostic — it is the component developers replace with their own model.

## `interruption_config.py` must not import `agora_agent`

The module is tested in isolation without the SDK on the path. Any `agora_agent` import would break the unit tests and violate the isolation invariant.

## Turn detection is set on `AgoraAgent`, not on a vendor

Unlike the realtime MLLM recipe (where `turn_detection` is vendor-owned), this cascading recipe sets `turn_detection={...}` directly on `AgoraAgent(...)`. The `interruption` dict is also set on `AgoraAgent(...)`, not on the `CustomLLM` vendor.

## Keep `/api/*` ownership in rewrites

Adding `web/app/api/**/route.ts` for agent/token logic breaks the boundary — `verify-api-contracts.ts` explicitly fails if a `route.ts` exists under `app/api`. Token logic belongs in `server/`.

## Agent is initialized at process start — missing env fails boot

Unlike the realtime recipe where `OPENAI_API_KEY` is validated lazily at `start()`, this recipe validates `AGORA_APP_ID`, `AGORA_APP_CERTIFICATE`, and `CUSTOM_LLM_URL` in `Agent.__init__`, which runs at server boot (`agent = Agent()` in `server.py`). A missing required var causes the server to log an exception and set `agent = None`; all routes then return 500. The `doctor:local` check catches this before `bun run dev`.

## camelCase request fields

`StartAgentRequest` uses `channelName`, `rtcUid`, `userUid` (camelCase) to match the browser client. Renaming one side without the other breaks the contract tests.

## Local calls under a global proxy

Global proxies (Clash, etc.) can break `localhost`/RFC-1918 traffic. Configure the proxy to send `127.0.0.1`, `localhost`, and private ranges DIRECT, or use `socksio` (in `requirements.txt`) plus `all_proxy` to route the backend through SOCKS.

## Related Deep Dives

- [interruption_config](L2/interruption_config.md) — correct interruption/VAD wiring.
- [mock_llm_endpoint](L2/mock_llm_endpoint.md) — CUSTOM_LLM_URL and SSE contract.
