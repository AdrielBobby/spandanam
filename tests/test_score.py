from viral.score import Score, Note, quantize, score_from_dict


def test_roundtrip_and_slice():
    d = {"title": "x", "bpm": 100, "beats_per_cycle": 8, "kit": "tabla", "notes": [{"beat": 0, "finger": 0}, {"beat": 9.5, "finger": 7, "label": "ta"}], "phrases": [[0, 8], [8, 16]]}
    s = score_from_dict(d)
    assert s.notes[1].finger == 2 and s.notes[1].label == "ta" and s.phrases == ((0.0, 8.0), (8.0, 16.0))
    sl = s.slice(8, 16); assert len(sl.notes) == 1 and sl.notes[0].beat == 1.5
    assert score_from_dict(__import__("json").loads(s.to_json())).notes == s.notes


def test_quantize():
    assert quantize([0.1, 0.9, 1.26]) == [0.0, 1.0, 1.25]
