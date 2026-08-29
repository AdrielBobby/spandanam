import json
from asan.gemma_asan import first_lesson, parse_hearing, parse_lesson


def test_parse_hearing_clamps_and_filters():
    h = parse_hearing(json.dumps({"played": ["tha", "xx", "ki"], "score": 140, "weak_strokes": [1], "rushing": True,
                                  "diagnosis_ml": "വേഗം കൂടുതൽ"}))
    assert h.played == ("tha", "ki") and h.score == 100 and h.rushing and h.weak_strokes == (1,)


def test_parse_lesson_falls_back_when_invalid():
    fb = first_lesson(60)
    l = parse_lesson(json.dumps({"phrase": ["zzz"], "bpm": 999, "say_ml": "x"}), fb)
    assert l.phrase == fb.phrase and l.bpm == 200
    l2 = parse_lesson(json.dumps({"phrase": ["tha", "ka", "dhi", "mi"], "bpm": 72, "focus": "left_hand"}), fb)
    assert l2.phrase == ("tha", "ka", "dhi", "mi") and l2.bpm == 72 and l2.focus == "left_hand"
