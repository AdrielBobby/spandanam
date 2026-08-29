from asan.analysis import PracticeAnalysis
from viral.bridge import analysis_for_coach, finger_syllables, phrase_to_score


def test_phrase_to_score_maps_fingers_and_cycles():
    sc = phrase_to_score(["dhim", "tha", "ka", "ta", "ki"], 80, cycles=2)
    assert len(sc.notes) == 10 and sc.beats_per_cycle == 5 and sc.phrases == ((0.0, 5.0), (5.0, 10.0))
    assert sc.notes[0].finger == 0 and sc.notes[0].label == "dhim"       # thumb
    assert sc.notes[1].finger == 1 and sc.notes[2].finger == 3            # index, ring
    assert sc.notes[5].beat == 5.0
    assert len(finger_syllables()) == 5 and all(finger_syllables())


def test_phrase_to_score_rejects_unknown():
    try:
        phrase_to_score(["boom"], 80); assert False
    except ValueError:
        pass


def test_analysis_for_coach_flattens():
    a = PracticeAnalysis(62.5, 16, ("ring", "pinky"), ("ki",), "late", 52, ("tha", "ki", "ta"), "Mostly late on ring finger.")
    d = analysis_for_coach(a, 60)
    assert d["accuracy"] == 0.625 and d["weak_fingers"] == ["ring", "pinky"] and d["recommended_bpm"] == 52 and d["current_bpm"] == 60


def test_judge_log_feeds_deterministic_analysis():
    from viral.bridge import analyze_attempt, judge_log_to_results
    sc = phrase_to_score(["dhim", "tha", "ka", "ta", "ki"], 120)
    log = ((0, "perfect", 5.0, 0), (1, "late", 110.0, 1), (2, "wrong_finger", 20.0, 0), (3, "miss", 0.0, 2), (None, "extra", 0.0, 4))
    rs = judge_log_to_results(sc, log)
    assert len(rs) == 5 and rs[1].timing_error_ms == 110 and rs[3].actual is None and rs[4].expected is None
    a = analyze_attempt(sc, log)
    assert a is not None and a.total_expected == 4 and "ring" in a.weak_fingers or "middle" in a.weak_fingers
    assert a.dominant_error in ("missed", "wrong_finger", "late")
