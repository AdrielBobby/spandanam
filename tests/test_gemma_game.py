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
