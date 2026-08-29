import pytest

from asan.analysis import _dominant_error, _rank_weaknesses, _recommended_tempo, analyze
from asan.input_sources import InputEvent
from asan.scheduler import build_schedule, score_events

PHRASE = ["dhim", "tha", "ka", "ta", "ki"]


# --- perfect round -----------------------------------------------------------------------

def test_perfect_round_has_no_weaknesses_and_bumps_tempo():
    schedule = build_schedule(PHRASE, 90)
    events = [InputEvent(e.expected_time_ms, e.finger, "test") for e in schedule]
    results = score_events(schedule, events)

    analysis = analyze(results, PHRASE, current_tempo_bpm=90)

    assert analysis.accepted_accuracy_pct == 100.0
    assert analysis.total_expected == 5
    assert analysis.weak_fingers == ()
    assert analysis.weak_bols == ()
    assert analysis.dominant_error == "none"
    assert analysis.recommended_tempo_bpm == 95  # 90 + 5, within [40, 120]
    assert analysis.recommended_phrase == tuple(PHRASE)
    assert "Perfect round" in analysis.deterministic_feedback


# --- mostly late, ring finger --------------------------------------------------------------

def test_mostly_late_ring_finger_ranks_ring_and_its_bols_first():
    schedule = build_schedule(PHRASE, 90)
    events = [
        InputEvent(schedule[0].expected_time_ms, schedule[0].finger, "test"),        # dhim/thumb on_time
        InputEvent(schedule[1].expected_time_ms, schedule[1].finger, "test"),        # tha/index on_time
        InputEvent(schedule[2].expected_time_ms + 200, schedule[2].finger, "test"),  # ka/ring correct_late
        InputEvent(schedule[3].expected_time_ms, schedule[3].finger, "test"),        # ta/middle on_time
        InputEvent(schedule[4].expected_time_ms + 200, schedule[4].finger, "test"),  # ki/ring correct_late
    ]
    results = score_events(schedule, events)

    analysis = analyze(results, PHRASE, current_tempo_bpm=90)

    assert analysis.weak_fingers == ("ring",)
    assert analysis.weak_bols == ("ka", "ki")  # tie at weight 1 each, "ka" occurs first
    assert analysis.dominant_error == "late"
    # accepted_accuracy_pct is 100% (correct_late is an accepted outcome) but
    # dominant_error != "none", so the >=95% bracket keeps tempo rather than bumping it.
    assert analysis.accepted_accuracy_pct == 100.0
    assert analysis.recommended_tempo_bpm == 90
    assert analysis.recommended_phrase == ("ka", "ki")


# --- missed-heavy ---------------------------------------------------------------------------

def test_missed_heavy_round_lowers_tempo():
    schedule = build_schedule(PHRASE, 70)
    results = score_events(schedule, [])  # nothing played -> every beat missed

    analysis = analyze(results, PHRASE, current_tempo_bpm=70)

    assert analysis.dominant_error == "missed"
    assert analysis.accepted_accuracy_pct == 0.0
    # ring covers both "ka" and "ki" (weight 3+3=6), so it outranks the single-beat
    # fingers (weight 3 each), which then tie-break by first occurrence: thumb, index, middle
    assert analysis.weak_fingers == ("ring", "thumb", "index", "middle")
    assert analysis.recommended_tempo_bpm == 50  # accuracy < 60% -> -20


# --- wrong-finger-heavy -----------------------------------------------------------------------

def test_wrong_finger_heavy_round():
    schedule = build_schedule(PHRASE, 90)
    wrong = {"thumb": "index", "index": "thumb", "middle": "thumb", "ring": "thumb"}
    events = [InputEvent(e.expected_time_ms, wrong[e.finger], "test") for e in schedule]
    results = score_events(schedule, events)

    analysis = analyze(results, PHRASE, current_tempo_bpm=90)

    assert analysis.dominant_error == "wrong_finger"
    assert analysis.accepted_accuracy_pct == 0.0
    assert analysis.recommended_tempo_bpm == 70  # accuracy < 60% -> -20


# --- extra-only vs. truly empty --------------------------------------------------------------

def test_extra_only_results_have_dominant_error_but_no_weaknesses():
    tap = InputEvent(9999, "thumb", "test")
    results = score_events((), [tap])  # nothing expected, one extra tap

    analysis = analyze(results, [], current_tempo_bpm=70)

    assert analysis.dominant_error == "extra"
    assert analysis.weak_fingers == ()
    assert analysis.weak_bols == ()
    assert analysis.total_expected == 0
    assert analysis.accepted_accuracy_pct == 0.0
    assert "extra taps" in analysis.deterministic_feedback
    assert "No beats were captured" not in analysis.deterministic_feedback


def test_completely_empty_results_are_handled_safely():
    analysis = analyze((), [], current_tempo_bpm=90)

    assert analysis.total_expected == 0
    assert analysis.accepted_accuracy_pct == 0.0
    assert analysis.weak_fingers == ()
    assert analysis.weak_bols == ()
    assert analysis.dominant_error == "none"
    assert analysis.deterministic_feedback == "No beats were captured this round, so there is nothing to analyze yet."


# --- tie ordering is deterministic ------------------------------------------------------------

def test_tie_ordering_uses_first_occurrence_not_dict_order():
    schedule = build_schedule(["tha", "ki"], 90)  # tha/index at beat0, ki/ring at beat1
    events = [
        InputEvent(schedule[0].expected_time_ms - 200, schedule[0].finger, "test"),  # index correct_early, weight 1
        InputEvent(schedule[1].expected_time_ms - 200, schedule[1].finger, "test"),  # ring correct_early, weight 1
    ]
    fingers, bols = _rank_weaknesses(score_events(schedule, events))
    assert fingers == ("index", "ring")  # equal weight; index occurs first in results order
    assert bols == ("tha", "ki")


# --- tempo clamping -----------------------------------------------------------------------------

def test_recommended_tempo_clamps_at_lower_bound():
    assert _recommended_tempo(current_tempo_bpm=45, accepted_accuracy_pct=10.0, dominant_error="missed") == 40


def test_recommended_tempo_clamps_at_upper_bound():
    assert _recommended_tempo(current_tempo_bpm=118, accepted_accuracy_pct=100.0, dominant_error="none") == 120


def test_recommended_tempo_brackets():
    assert _recommended_tempo(100, 59.9, "missed") == 80        # <60% -> -20
    assert _recommended_tempo(100, 60.0, "missed") == 90        # 60-<80% -> -10
    assert _recommended_tempo(100, 79.9, "missed") == 90        # 60-<80% -> -10
    assert _recommended_tempo(100, 80.0, "missed") == 100       # 80-<95% -> keep
    assert _recommended_tempo(100, 94.9, "missed") == 100       # 80-<95% -> keep
    assert _recommended_tempo(100, 95.0, "none") == 105         # >=95% and none -> +5
    assert _recommended_tempo(100, 95.0, "wrong_finger") == 100 # >=95% but not none -> keep


# --- invalid input -------------------------------------------------------------------------------

def test_analyze_rejects_non_positive_current_tempo():
    with pytest.raises(ValueError, match="current_tempo_bpm"):
        analyze((), [], current_tempo_bpm=0)
    with pytest.raises(ValueError, match="current_tempo_bpm"):
        analyze((), [], current_tempo_bpm=-10)


# --- dominant_error helper (direct) ---------------------------------------------------------------

def test_dominant_error_none_when_all_on_time_and_no_extras():
    schedule = build_schedule(PHRASE, 90)
    events = [InputEvent(e.expected_time_ms, e.finger, "test") for e in schedule]
    assert _dominant_error(score_events(schedule, events)) == "none"


# --- purity: no clock, hardware, keyboard, or model dependency ------------------------------------

def test_analysis_module_has_no_clock_hardware_or_model_imports():
    import asan.analysis as analysis_module

    for forbidden in ("time", "msvcrt", "httpx", "platform", "genai"):
        assert forbidden not in vars(analysis_module)
