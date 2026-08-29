import json
from spandanam.gemma_ear import parse_hearing, DEFAULT_HEARING


def test_parse_full_hearing_and_clamps():
    h = parse_hearing(json.dumps({
        "instruments": ["valanthala", "kombu"], "kaalam": 3, "event": "kombu_solo",
        "body_map": {"bass": ["chest", "bogus"], "horn": ["l_shoulder", "r_shoulder"]},
        "gains": {"bass": 9, "horn": 1.2}, "motif": {"back": 999, "nope": 5},
        "caption_en": "Kombu solo", "caption_ml": "കൊമ്പ് സോളോ"}))
    assert h.body_map["bass"] == ("chest",) and h.gains["bass"] == 1.5
    assert h.motif == {"back": 255} and h.event == "kombu_solo" and h.kaalam == 3


def test_parse_minimal_falls_back_to_defaults():
    h = parse_hearing("{}")
    assert h.body_map == DEFAULT_HEARING.body_map and h.gains["bass"] == 1.0
