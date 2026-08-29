import json
from viral.gemma_game import ladder_round, parse_round, LADDER


def test_ladder_clamps_and_is_playable():
    assert ladder_round(0).level == 0 and ladder_round(99).phrase == tuple(LADDER[-1][0])
    r = ladder_round(3); assert len(r.phrase) >= 3 and r.source == "ladder"


def test_parse_round_filters_and_clamps():
    r = parse_round(json.dumps({"phrase": ["tha", "boom", "ki", "ta"], "bpm": 999, "banter": "Sheri!"}), 2)
    assert r.phrase == ("tha", "ki", "ta") and r.bpm == 160 and r.source == "gemma"
    assert parse_round(json.dumps({"phrase": ["tha"]}), 1) is None
