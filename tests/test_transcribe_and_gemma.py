import json
import numpy as np
from viral.transcribe import kmeans_1d, onsets_to_beats, Transcription, Onset
from viral.gemma_thaalam import default_structure, parse_structure
from viral.learn import build_score


def test_kmeans_orders_low_to_high():
    x = np.array([1, 1.1, 5, 5.2, 9, 9.1, 13, 13.1, 17, 17.2])
    lab = kmeans_1d(x, 5)
    assert list(lab) == [0, 0, 1, 1, 2, 2, 3, 3, 4, 4]


def test_onsets_to_beats_quantised():
    tr = Transcription(120.0, (Onset(1.0, 0, 1, 100), Onset(1.26, 1, .5, 300), Onset(2.0, 2, .8, 900)), {}, 3.0)
    ev = onsets_to_beats(tr, 120.0)
    assert ev == [(0.0, 0, 1.0), (0.5, 1, 0.5), (2.0, 2, 0.8)]


def test_structure_parse_and_build_score():
    fb = default_structure(90, 16)
    st = parse_structure(json.dumps({"title": "Panchari", "thaalam": "panchari (6)", "beats_per_cycle": 6, "kit": "chenda",
        "finger_map": {"cluster_to_finger": {"0": 4, "1": 3, "2": 2, "3": 1, "4": 0}, "names": ["a", "b", "c", "d", "e"], "syllables": ["tha", "ki", "ta", "ka", "dhi"]},
        "phrases": [[0, 6], [6, 12]]}), fb)
    assert st.cluster_to_finger[0] == 4 and st.beats_per_cycle == 6
    sc = build_score([(0.0, 0, 1.0), (1.0, 4, 0.5)], st, 90)
    assert sc.notes[0].finger == 4 and sc.notes[0].label == "dhi" and sc.notes[1].finger == 0 and sc.thaalam == "panchari (6)"
    assert parse_structure("{}", fb).kit == "chenda"


def test_normalize_misspelled_keys_and_auto_phrases():
    from viral.gemma_thaalam import auto_phrases, normalize_keys
    d = normalize_keys({"kaaalam": 2, "finger_map": {"syllaibles": ["a"], "cluster_to_fingr": {"0": 1}}, "phrses": [[0, 8]]})
    assert d["kaalam"] == 2 and d["finger_map"]["syllables"] == ["a"] and d["finger_map"]["cluster_to_finger"] == {"0": 1} and "phrases" in d
    assert auto_phrases(32, 8) == ((0.0, 8.0), (0.0, 16.0), (0.0, 32.0))
    assert auto_phrases(6, 6) == ((0.0, 6.0),)
    fb = default_structure(90, 32)
    st = parse_structure(json.dumps({"beats_per_cycle": 8, "phrases": [[0, 8]]}), fb)
    assert len(st.phrases) >= 2
