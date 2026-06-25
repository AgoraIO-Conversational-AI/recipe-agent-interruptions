# Deep Dive — Mock LLM Endpoint

> **When to Read This:** You are replacing the mock with a real model, debugging LLM turn failures (agent starts but never speaks), or wiring a new endpoint. For the architecture context, start at [02_architecture](../02_architecture.md).

The mock LLM endpoint (`server/src/llm.py`) is an OpenAI-compatible `POST /chat/completions` handler mounted at `/llm` in the same FastAPI process as the agent backend. It always returns a long monologue so you have time to practice interrupting the agent. It has no `agora_agent` dependency and is the component you replace.

## The endpoint

`POST /llm/chat/completions` (mounted under `/llm` in `server.py`)

- Accepts an OpenAI `ChatCompletionRequest` with `stream: true` (streaming is required; `stream: false` returns 400).
- Returns a `StreamingResponse` with `media_type="text/event-stream"`.
- Agora cloud sends `Authorization: Bearer <CUSTOM_LLM_API_KEY>`; the mock logs but does not validate it.

## SSE response format

Each chunk follows the OpenAI streaming format:

```
data: {"id":"chatcmpl-...","object":"chat.completion.chunk","created":...,"model":"...","choices":[{"index":0,"delta":{"role":"assistant","content":""},"finish_reason":null}]}

data: {"id":"chatcmpl-...","object":"chat.completion.chunk","created":...,"model":"...","choices":[{"index":0,"delta":{"content":"Sure,"},"finish_reason":null}]}

...

data: {"id":"chatcmpl-...","object":"chat.completion.chunk","created":...,"model":"...","choices":[{"index":0,"delta":{},"finish_reason":"stop"}]}

data: [DONE]
```

Chunk sequence:
1. A role chunk (`delta: { "role": "assistant", "content": "" }`)
2. Content chunks, one word at a time with a 50ms delay between each
3. A finish chunk (`delta: {}`, `finish_reason: "stop"`)
4. `data: [DONE]`

This format must be preserved exactly when replacing the mock.

## The mock reply logic

```python
MONOLOGUE = "Sure, let me tell you a long and winding story..."  # ~150 words

def get_long_reply(messages: list) -> str:
    return MONOLOGUE
```

`get_long_reply()` ignores the conversation history — the monologue is always the same. This is intentional: the recipe is about interruption behavior, not LLM content.

## Replacing the mock

Replace the body of `get_long_reply()` with your own model logic. The function receives the full message list (`messages: list`) and must return a string.

```python
def get_long_reply(messages: list) -> str:
    # Example: call a local Ollama model
    import requests
    resp = requests.post("http://localhost:11434/api/generate", json={
        "model": "llama3",
        "prompt": messages[-1]["content"] if messages else "",
    })
    return resp.json()["response"]
```

Requirements for a production replacement:
- Keep the OpenAI SSE streaming contract (`data: {...}\n\n`, ending with `data: [DONE]\n\n`).
- Keep `llm.py` free of `agora_agent` imports (enforced by `test_llm_mount.py`).
- Validate the `Authorization: Bearer` header if your endpoint is publicly reachable.
- Set `CUSTOM_LLM_URL` to the public URL of the new endpoint.

## How `CUSTOM_LLM_URL` connects the agent to the endpoint

In `Agent.__init__()`:

```python
self.custom_llm_url = os.getenv("CUSTOM_LLM_URL")   # must be public; no localhost default
```

In `Agent.start()`:

```python
llm = CustomLLM(
    base_url=self.custom_llm_url,
    api_key=self.custom_llm_api_key,
    model=self.custom_llm_model,
    ...
)
```

`CustomLLM` stamps `vendor: "custom"` in the Agora wire config. Agora cloud then POSTs to `CUSTOM_LLM_URL` (not the browser-facing backend URL; the two coincide in this recipe because the mock is co-hosted, but they are logically separate).

## Hosting the endpoint separately

If you replace the mock with a separate service (e.g. a different server, a cloud function, or an API proxy):
1. Deploy it separately and get its public URL.
2. Set `CUSTOM_LLM_URL` to that URL (e.g. `https://my-llm.example.com/chat/completions`).
3. The `/llm` mount in `server.py` can be removed if no longer needed, but this is optional.

## Related L1

- [02_architecture](../02_architecture.md) · [06_interfaces](../06_interfaces.md) · [07_gotchas](../07_gotchas.md)
