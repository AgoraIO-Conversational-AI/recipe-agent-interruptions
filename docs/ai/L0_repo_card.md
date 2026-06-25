# recipe-agent-interruptions — Repo Card

> Next.js web client + Python FastAPI backend for an Agora Conversational AI voice agent with configurable barge-in behavior: fully interruptible, uninterruptable, or keyword-triggered. Uses a cascading STT/LLM/TTS pipeline with a zero-key mock LLM endpoint co-hosted in the same process.

## Identity

| Field          | Value                                                                        |
| -------------- | ---------------------------------------------------------------------------- |
| Repo           | `AgoraIO-Conversational-AI/recipe-agent-interruptions`                       |
| Type           | `distributed-system` (single repo, two co-located processes, one port)       |
| Language       | Python 3.10+ (FastAPI + uvicorn) backend + Next.js 16 / React 19 web         |
| Deploy Target  | `web/` as Next.js app, `server/` as a publicly reachable FastAPI service     |
| Owner          | Agora Conversational AI DevEx                                                |
| Last Reviewed  | 2026-06-25                                                                   |
| Recipe Role    | `base`                                                                       |
| Recipe Version | `1.0.0`                                                                      |
| Recipe Status  | `experimental`                                                               |

## L1 — Summaries

The Audience column helps agents prioritise: **Use** = consuming the recipe's behavior, **Maintain** = modifying internals.

| File                                     | Purpose                                                                          | Audience       |
| ---------------------------------------- | -------------------------------------------------------------------------------- | -------------- |
| [01_setup](L1/01_setup.md)               | bun + venv + pip setup, env vars (incl. required `CUSTOM_LLM_URL`), commands    | Use & Maintain |
| [02_architecture](L1/02_architecture.md) | Two-concern topology, rewrite proxy, cascading pipeline, mock LLM co-host        | Maintain       |
| [03_code_map](L1/03_code_map.md)         | `web/` and `server/` trees with key file responsibilities                        | Maintain       |
| [04_conventions](L1/04_conventions.md)   | Python async + FastAPI patterns, interruption config isolation, response envelope | Maintain       |
| [05_workflows](L1/05_workflows.md)       | Change interruption mode, replace mock LLM, add a route, verify, deploy          | Use            |
| [06_interfaces](L1/06_interfaces.md)     | FastAPI route contracts, rewrites, env vars, interruption config dict shapes     | Use & Maintain |
| [07_gotchas](L1/07_gotchas.md)           | Public tunnel required, `CUSTOM_LLM_URL` no-localhost, `PORT` in env             | Maintain       |
| [08_security](L1/08_security.md)         | Token007, App Certificate server-only, co-public `/llm`, CORS, auth caveat       | Maintain       |

## Recipe Profile

This repo declares `Recipe Role: base`. See [RECIPE.md](RECIPE.md) for extension points, invariants, and stable contracts before changing reusable surfaces.
