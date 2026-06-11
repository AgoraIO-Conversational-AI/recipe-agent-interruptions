"""Maps INTERRUPTION_MODE → the Agora `interruption` config dict.

Kept free of `agora_agent` imports so it is unit-testable without the SDK.
"""
from typing import Any, Dict, Optional


def build_interruption_config(mode: Optional[str]) -> Dict[str, Any]:
    mode = (mode or "interruptible").strip().lower()
    if mode == "uninterruptable":
        return {"enable": False, "disabled_config": {"strategy": "append"}}
    if mode == "keywords":
        return {
            "enable": True,
            "mode": "keywords",
            "keywords_config": {"keywords": ["stop", "wait", "hold on"]},
        }
    return {"enable": True}
