# Deep Dive — Interruption Config and VAD Tuning

> **When to Read This:** You are changing the interruption behavior, adding a new interruption mode, or adjusting VAD (voice activity detection) thresholds and timings. For the high-level picture, start at [02_architecture](../02_architecture.md).

This recipe's core feature is the `interruption` config applied to `AgoraAgent` at session start. It controls whether and how the user's speech stops the agent mid-sentence. VAD (turn detection) is a separate config that governs how the pipeline detects speech boundaries.

## The interruption config builder

`build_interruption_config(mode: str | None) → dict` lives in `server/src/interruption_config.py`. It has **no `agora_agent` import** and is unit-testable in isolation.

```python
def build_interruption_config(mode):
    mode = (mode or "interruptible").strip().lower()
    if mode == "uninterruptable":
        return {"enable": False, "disabled_config": {"strategy": "append"}}
    if mode == "keywords":
        return {
            "enable": True,
            "mode": "keywords",
            "keywords_config": {"keywords": ["stop", "wait", "hold on"]},
        }
    return {"enable": True}    # interruptible (default) + any unknown mode
```

## Interruption modes

| Mode (`INTERRUPTION_MODE`) | `interruption` dict sent to Agora | Behavior |
| -------------------------- | --------------------------------- | -------- |
| `interruptible` (default)  | `{"enable": True}` | Agent stops speaking as soon as user speech is detected. |
| `uninterruptable`          | `{"enable": False, "disabled_config": {"strategy": "append"}}` | Agent finishes its entire turn; user speech is queued and appended to the next turn. |
| `keywords`                 | `{"enable": True, "mode": "keywords", "keywords_config": {"keywords": ["stop", "wait", "hold on"]}}` | Agent stops only when a recognized trigger word is detected. |
| any other / `None`         | `{"enable": True}` | Falls through to interruptible. |

Mode matching is case-insensitive (`.lower()`) and leading/trailing whitespace is stripped.

## How it is wired into the session

In `Agent.start()` (`server/src/agent.py`):

```python
agora_agent = AgoraAgent(
    client=self.client,
    instructions=CUSTOM_LLM_PROMPT,
    greeting=self.greeting,
    failure_message="Please wait a moment.",
    max_history=50,
    interruption=build_interruption_config(self.interruption_mode),
    turn_detection={...},   # see VAD section below
    advanced_features={"enable_rtm": True},
    parameters=parameters,
)
agora_agent = agora_agent.with_stt(stt).with_llm(llm).with_tts(tts)
```

`interruption` and `turn_detection` are both set on `AgoraAgent`, not on individual vendors.

## VAD / turn detection config

The `turn_detection` dict passed to `AgoraAgent(...)`:

```python
{
    "config": {
        "speech_threshold": 0.5,
        "start_of_speech": {
            "mode": "vad",
            "vad_config": {
                "interrupt_duration_ms": 160,   # how long user must speak to trigger start-of-speech
                "prefix_padding_ms": 300,        # audio buffered before the speech boundary
            },
        },
        "end_of_speech": {
            "mode": "vad",
            "vad_config": {
                "silence_duration_ms": 480,      # silence duration to trigger end-of-speech
            },
        },
    },
}
```

### Tuning guidance

| Parameter | Effect of increasing | Effect of decreasing |
| --------- | -------------------- | -------------------- |
| `speech_threshold` | Less sensitive to quiet voices; reduces false triggers | More sensitive; may trigger on background noise |
| `interrupt_duration_ms` | User must speak longer before an interruption fires | Interruptions fire faster; may clip short filler words |
| `prefix_padding_ms` | More audio context buffered at speech start | Less context; first word may be clipped in STT |
| `silence_duration_ms` | Agent waits longer before treating pause as end-of-turn | Agent treats short pauses as end-of-turn; may cut off slow speakers |

## Adding a new interruption mode

1. Add a new branch in `build_interruption_config()` with the new mode string and the Agora `interruption` dict shape.
2. Add a test in `server/tests/test_interruption_config.py` covering the new mode and edge cases.
3. Document the new `INTERRUPTION_MODE` value in `server/.env.example` and the root `README.md`.
4. Verify: `cd server && pytest tests/test_interruption_config.py -v`.

## Customizing keyword triggers

To change the trigger words for `keywords` mode, edit the `keywords_config.keywords` list in `build_interruption_config()`:

```python
if mode == "keywords":
    return {
        "enable": True,
        "mode": "keywords",
        "keywords_config": {"keywords": ["stop", "wait", "hold on"]},  # edit this list
    }
```

## Related L1

- [02_architecture](../02_architecture.md) · [06_interfaces](../06_interfaces.md) · [07_gotchas](../07_gotchas.md)
