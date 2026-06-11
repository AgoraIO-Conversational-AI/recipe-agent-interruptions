import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import interruption_config as ic  # noqa: E402


def test_interruptible_default():
    assert ic.build_interruption_config(None) == {"enable": True}
    assert ic.build_interruption_config("interruptible") == {"enable": True}


def test_uninterruptable():
    assert ic.build_interruption_config("uninterruptable") == {
        "enable": False,
        "disabled_config": {"strategy": "append"},
    }


def test_keywords():
    cfg = ic.build_interruption_config("keywords")
    assert cfg["enable"] is True
    assert cfg["mode"] == "keywords"
    assert "stop" in cfg["keywords_config"]["keywords"]


def test_unknown_mode_defaults_to_interruptible():
    assert ic.build_interruption_config("bogus") == {"enable": True}


def test_mode_is_case_insensitive():
    assert ic.build_interruption_config("KEYWORDS")["mode"] == "keywords"
    assert ic.build_interruption_config("Uninterruptable")["enable"] is False
