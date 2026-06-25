# Docs Test Results

> Generated: 2026-06-25 | Repo: `AgoraIO-Conversational-AI/recipe-agent-interruptions`

## Structural Checks

| Check | Result |
| ----- | ------ |
| `docs/ai/L0_repo_card.md` present | Pass |
| `docs/ai/L0_repo_card.md` ≤ 50 lines | Pass (36 lines) |
| `docs/ai/RECIPE.md` present | Pass |
| `docs/ai/L1/` has exactly 8 files (`01`–`08`) | Pass (8 files) |
| `docs/ai/L1/L2/_index.md` present | Pass |
| L2 deep dives present (2) | Pass |
| `AGENTS.md` has `## How to Load` section | Pass |
| `AGENTS.md` has `## Git Conventions` section | Pass |
| `AGENTS.md` has `## Doc Commands` section | Pass |
| `AGENTS.md` Recipe Role is `base` | Pass |
| Stale "docs/ai not present" note removed from `AGENTS.md` | Pass |

## Relative Link Check

All relative links in `docs/ai/` were resolved against the filesystem. Counts:

| Source | Links checked | Broken |
| ------ | ------------- | ------ |
| `L0_repo_card.md` | 9 | 0 |
| `L1/L2/_index.md` | 2 | 0 |
| `L1/0*.md` (all 8 L1 files, Related Deep Dives) | 17 | 0 |
| **Total** | **28** | **0** |

## Backend Tests (pytest)

Ran in a throwaway venv at `/tmp/v_interruptions` (Python 3.14.4, pytest 9.1.1):

```
install: pip install -r server/requirements.txt -r server/requirements-dev.txt
command: cd server && pytest tests -v
```

| Test | Result |
| ---- | ------ |
| `test_agent_construction.py::test_start_constructs_real_agent_and_returns_shape` | Pass |
| `test_interruption_config.py::test_interruptible_default` | Pass |
| `test_interruption_config.py::test_uninterruptable` | Pass |
| `test_interruption_config.py::test_keywords` | Pass |
| `test_interruption_config.py::test_unknown_mode_defaults_to_interruptible` | Pass |
| `test_interruption_config.py::test_mode_is_case_insensitive` | Pass |
| `test_llm.py::test_health` | Pass |
| `test_llm.py::test_streaming_sse_contract` | Pass |
| `test_llm.py::test_non_streaming_rejected` | Pass |
| `test_llm_mount.py::test_llm_health_is_mounted_under_slash_llm` | Pass |
| `test_llm_mount.py::test_llm_chat_completions_reachable_through_mount` | Pass |
| `test_llm_mount.py::test_llm_module_has_no_agora_dependency` | Pass |

**12 passed, 0 failed, 1 warning** (starlette deprecation warning for `httpx`; not a test failure).

The throwaway venv was removed after the run (`rm -rf /tmp/v_interruptions`).

## Q&A Verification (≥12 across 5 categories)

Each answer was verified against source files before marking Pass.

### Category A — Identity / Setup

| # | Question | Answer | Source | Result |
| - | -------- | ------ | ------ | ------ |
| 1 | What is the default value of `INTERRUPTION_MODE`? | `interruptible` | `server/src/agent.py` line 45: `os.getenv("INTERRUPTION_MODE", "interruptible")` | Pass |
| 2 | Why is `CUSTOM_LLM_URL` required and cannot be localhost? | Agora cloud — not the browser or the backend — calls `CUSTOM_LLM_URL` directly; a localhost URL is unreachable from the cloud. `Agent.__init__` raises `ValueError` if unset. | `server/src/agent.py` lines 54–65 | Pass |
| 3 | What command sets up the Python venv and installs deps? | `bun run setup` | `package.json` `setup` script | Pass |

### Category B — Architecture / Pipeline

| # | Question | Answer | Source | Result |
| - | -------- | ------ | ------ | ------ |
| 4 | What STT and TTS vendors are used? | `DeepgramSTT(model="nova-3", language="en")` and `MiniMaxTTS(model="speech_2_6_turbo", voice_id="English_captivating_female1")` | `server/src/agent.py` lines 123–124 | Pass |
| 5 | How is the mock LLM endpoint mounted in the server? | `app.mount("/llm", llm_app)` in `server/src/server.py`. Agora cloud reaches it at `<public-url>/llm/chat/completions`. | `server/src/server.py` line 198 | Pass |
| 6 | Does the mock LLM have any `agora_agent` imports? | No. This is enforced by `test_llm_mount.py::test_llm_module_has_no_agora_dependency` (AST walk). | `server/src/llm.py` (no `agora` import) + `server/tests/test_llm_mount.py` lines 18–32 | Pass |

### Category C — Interruption Config

| # | Question | Answer | Source | Result |
| - | -------- | ------ | ------ | ------ |
| 7 | What Agora config does `uninterruptable` mode produce? | `{"enable": False, "disabled_config": {"strategy": "append"}}` | `server/src/interruption_config.py` lines 10–11 | Pass |
| 8 | What are the default keyword triggers for `keywords` mode? | `["stop", "wait", "hold on"]` | `server/src/interruption_config.py` lines 12–17 | Pass |
| 9 | Where is `turn_detection` (VAD) set, and what is the default `silence_duration_ms`? | On `AgoraAgent(turn_detection={...})` in `agent.py`; `silence_duration_ms: 480`. | `server/src/agent.py` lines 141–159 | Pass |

### Category D — Interfaces / Contracts

| # | Question | Answer | Source | Result |
| - | -------- | ------ | ------ | ------ |
| 10 | What does `POST /startAgent` return on success? | `{"code": 0, "msg": "success", "data": {"agent_id": ..., "channel_name": ..., "status": "started"}}` | `server/src/server.py` line 164, `server/src/agent.py` lines 208–212 | Pass |
| 11 | Does `POST /stopAgent` return a `data` field? | No. It returns `{"code": 0, "msg": "success"}` with no `data`. | `server/src/server.py` line 188 | Pass |
| 12 | What does the browser call to start a conversation, and where is it routed? | Browser calls `POST /api/startAgent`; Next.js rewrites it to `POST /startAgent` on the backend. | `web/next.config.ts` lines 26–29, `web/src/services/api.ts` lines 37–56 | Pass |

### Category E — Security / Gotchas

| # | Question | Answer | Source | Result |
| - | -------- | ------ | ------ | ------ |
| 13 | Why must `PORT` not appear in `server/.env.example`? | `verify:local:fastapi` injects a random `PORT` via `load_dotenv(override=True)`. A `PORT` in `.env.example` (copied to `.env.local`) would clobber the injected port and break the smoke test. | `package.json` `verify:local:fastapi` script; `server/scripts/run_fake_server.py` line 39 | Pass |
| 14 | Are the token endpoints co-public with the LLM endpoint? | Yes. Both share port 8000 and a single publicly reachable process. The App Certificate is used only in-memory and never crosses a wire, but `/get_config` and `/startAgent` are unauthenticated in this recipe. Auth/rate-limiting must be added before production. | `ARCHITECTURE.md` lines 40–48 | Pass |

## Summary by Category

| Category | Questions | Passed | Failed |
| -------- | --------- | ------ | ------ |
| A — Identity / Setup | 3 | 3 | 0 |
| B — Architecture / Pipeline | 3 | 3 | 0 |
| C — Interruption Config | 3 | 3 | 0 |
| D — Interfaces / Contracts | 3 | 3 | 0 |
| E — Security / Gotchas | 2 | 2 | 0 |
| **Total** | **14** | **14** | **0** |

## Fix / Retest

No failures found. No fixes required.
