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
