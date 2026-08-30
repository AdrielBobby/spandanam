import json
from viral.gemma_game import ladder_round, parse_round, LADDER


def test_ladder_clamps_and_is_playable():
    assert ladder_round(0).level == 0 and ladder_round(99).phrase == tuple(LADDER[-1][0])
    r = ladder_round(3); assert len(r.phrase) >= 3 and r.source == "ladder"


def test_parse_round_filters_and_clamps():
    r = parse_round(json.dumps({"phrase": ["tha", "boom", "ki", "ta"], "bpm": 999, "banter": "Sheri!"}), 2)
    assert r.phrase == ("tha", "ki", "ta") and r.bpm == 160 and r.source == "gemma"
    assert parse_round(json.dumps({"phrase": ["tha"]}), 1) is None


def test_normalize_keeps_phrase_distinct_from_phrases():
    from viral.gemma_thaalam import normalize_keys
    d = normalize_keys({"phrase": ["tha"], "phrases": [[0, 8]]})
    assert d["phrase"] == ["tha"] and d["phrases"] == [[0, 8]]


def test_parse_round_enforces_level_target_and_novelty():
    from viral.gemma_game import level_target
    assert level_target(1) == {"syllables": 3, "bpm": 60, "min_distinct_fingers": 2}
    assert level_target(6)["syllables"] == 8 and level_target(9)["bpm"] == 160
    ok = json.dumps({"phrase": ["dhim", "tha", "ka", "ta"], "bpm": 80})
    assert parse_round(ok, 2) is not None
    assert parse_round(ok, 6) is None                                    # far too short for level 6
    assert parse_round(json.dumps({"phrase": ["tha", "tha", "tha"]}), 1) is None   # one finger only
    assert parse_round(ok, 2, previous=[["dhim", "tha", "ka", "ta"]]) is None      # repeat


def test_small_model_detection():
    from viral.gemma_thaalam import is_small_model
    assert is_small_model("gemma3:1b") and is_small_model("gemma3n:e2b") and not is_small_model("gemma3n:e4b")


def test_small_model_coach_coerces_junk_fields(monkeypatch):
    import asyncio, json
    import viral.gemma_thaalam as gt
    async def fake_chat(*a, **k):
        return json.dumps({"key_en": "Focus on the ring finger for 'ka' at 72 bpm.", "drill_phrase": "a, a, a", "drill_bpm": None, "focus": "vibes"})
    monkeypatch.setattr(gt, "_chat", fake_chat)
    fb = asyncio.run(gt.coach(None, "u", "gemma3:1b", {"accuracy": .62, "recommended_bpm": 72}, (), ()))
    assert fb["say_en"].startswith("Focus") and fb["drill_phrase"] == 0 and fb["drill_bpm"] == 72 and fb["focus"] == "timing"


def test_parse_engines_and_hub_engine_modes(monkeypatch):
    from viral.config import parse_engines, Config
    eng = parse_engines("laptop=http://127.0.0.1:11435|gemma3n:e4b, pi=http://127.0.0.1:11434|gemma3:1b")
    assert eng["laptop"]["model"] == "gemma3n:e4b" and eng["pi"]["url"].endswith("11434") and parse_engines(None) == {}
    monkeypatch.setattr("viral.server.Sampler", type("S", (), {"__init__": lambda self, k, assets=None: None, "set_kit": lambda *a, **k: None, "play": lambda *a, **k: None, "stop": lambda *a, **k: None, "kit": "chenda", "mixer": None}))
    from viral.server import Hub
    h = Hub(Config(dry=True, gemma_engines=eng))
    assert h.engine_mode == "laptop" and h.active_engines() == ["laptop"] and h.engine()["on_device"] is False
    h.engine_mode = "both"; assert h.active_engines() == ["laptop", "pi"] and h.engine("pi")["on_device"] is True
    h.engine_mode = "nope"; assert h.active_engines() == ["laptop"]
    h2 = Hub(Config(dry=True)); assert list(h2.engines) == ["primary"] and h2.active_engines() == ["primary"]
