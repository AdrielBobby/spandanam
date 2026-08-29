import pytest

from asan.config import FINGERS
from asan.input_sources import (
    KEY_FINGER_MAP,
    KeyboardSimulator,
    InputEvent,
    is_quit_key,
    normalize_key,
)


def test_key_finger_map_matches_config_fingers_in_order():
    assert list(KEY_FINGER_MAP.items()) == list(zip("12345", FINGERS))


def test_normalize_key_unknown_key_returns_none():
    assert normalize_key("x") is None
    assert normalize_key("0") is None
    assert normalize_key("") is None


@pytest.mark.parametrize("key", ["1", "2", "3", "4", "5"])
def test_normalize_key_emits_required_normalized_fields(key):
    event = normalize_key(key)
    assert isinstance(event, InputEvent)
    assert event.as_dict().keys() == {"timestamp_ms", "finger", "source", "strength"}
    assert event.source == "keyboard_simulator"
    assert event.strength == 1.0


def test_normalize_key_timestamp_is_integer():
    assert isinstance(normalize_key("1").timestamp_ms, int)
    assert normalize_key("1", now_ms=42).timestamp_ms == 42
    assert isinstance(normalize_key("1", now_ms=42).timestamp_ms, int)


@pytest.mark.parametrize("key", ["1", "2", "3", "4", "5"])
def test_normalize_key_finger_is_always_a_configured_finger(key):
    assert normalize_key(key).finger in FINGERS


def test_is_quit_key():
    assert is_quit_key("q") and is_quit_key("Q") and is_quit_key("\x1b")
    assert not is_quit_key("1") and not is_quit_key("x")


def test_keyboard_simulator_rejects_non_windows(monkeypatch):
    monkeypatch.setattr("asan.input_sources.platform.system", lambda: "Linux")
    with pytest.raises(RuntimeError, match="Windows"):
        next(KeyboardSimulator().events())
