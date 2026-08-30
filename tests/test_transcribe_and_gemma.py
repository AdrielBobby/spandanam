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


def test_repair_json_handles_truncation_fences_and_trailing_commas():
    from viral.gemma_thaalam import repair_json
    assert json.loads(repair_json('```json\n{"a": 1, "b": [1, 2,]}\n```')) == {"a": 1, "b": [1, 2]}
    d = json.loads(repair_json('{"title": "x", "phrases": [[0, 8], [8, 16'))
    assert d["title"] == "x" and d["phrases"][0] == [0, 8]
    d = json.loads(repair_json('{"title": "x", "notes_en": "cut off mid sen'))
    assert d["title"] == "x"
    assert repair_json('{"ok": true}') == '{"ok": true}'


def test_cycle_scores_prefer_true_period_and_digest_is_small():
    from viral.transcribe import cycle_scores, digest
    # 8-beat repeating pattern over 6 cycles
    pat = [(0, 0, 1.0), (0.5, 2, .6), (1, 1, .8), (2, 0, .9), (2.5, 3, .6), (3, 1, .8), (3.5, 4, .4),
           (4, 0, 1.0), (5, 1, .8), (6, 0, .9), (6.5, 3, .6), (7, 1, .8)]
    ev = [(b + 8 * c, k, s) for c in range(6) for b, k, s in pat]
    cs = cycle_scores(ev)
    assert cs[8] >= cs[6] and cs[8] >= cs[7] and cs[8] > 0.5
    d = digest(96, {0: {"count": 12}}, ev)
    assert d["best_cycle_guess"] in (4, 8) and d["evidence_strength"] in ("strong", "weak") and len(json.dumps(d)) < 2500 and d["n_events"] == 72


def test_cluster_periodicity_separates_true_cycle_and_pick_cycle():
    from viral.transcribe import cluster_cycle_scores, pick_cycle
    # 8-beat pattern whose halves DIFFER (so 8 is the true period, not 4)
    pat = [(0, 0), (1, 1), (2, 2), (3, 1), (4, 0), (5, 3), (6, 4), (7, 3)]
    ev = [(b + 8 * c, k, 1.0) for c in range(8) for b, k in pat]
    cs = cluster_cycle_scores(ev)
    assert cs[8] > 0.8 and cs[8] > cs[4] + 0.3 and cs[8] > cs[6] + 0.3 and cs[16] > 0.5
    assert pick_cycle(cs) == 8                                  # shortest within tolerance = the true period
    assert pick_cycle({4: 0.9, 8: 0.2}) == 4 and pick_cycle({}) == 8 and pick_cycle({4: 0.5, 8: 0.9, 16: 0.85}) == 8


def test_cycle_scores_handle_beats_that_round_up():
    from viral.transcribe import cycle_scores, cluster_cycle_scores
    ev = [(i * 0.5 + 0.13, i % 3, 0.9) for i in range(40)]      # 0.13 offsets are off-grid; last beat rounds up
    assert set(cycle_scores(ev)) and set(cluster_cycle_scores(ev))


def test_repair_json_keeps_text_of_unterminated_string():
    from viral.gemma_thaalam import repair_json
    d = json.loads(repair_json('{"say_en": "Okay, let us work on the ring finger at 72 bpm'))
    assert d["say_en"].startswith("Okay, let us work")
