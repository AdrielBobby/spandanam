import pytest

from asan.config import FINGERS, SYLLABLE_FINGER
from asan.input_sources import InputEvent
from asan.scheduler import (
    ExpectedEvent,
    Outcome,
    TimingWindow,
    UnsupportedSyllableError,
    beat_duration_ms,
    build_schedule,
    score_events,
)

PHRASE = ["dhim", "tha", "ka", "ta", "ki"]


# --- beat_duration_ms / schedule timing ----------------------------------------------

def test_beat_duration_ms_60_and_120_bpm():
    assert beat_duration_ms(60) == 1000
    assert beat_duration_ms(120) == 500


def test_build_schedule_timing_60bpm():
    schedule = build_schedule(PHRASE, 60, start_time_ms=500)
    assert [e.expected_time_ms for e in schedule] == [500, 1500, 2500, 3500, 4500]
    assert all(e.duration_ms == 1000 for e in schedule)
    assert [e.beat_index for e in schedule] == [0, 1, 2, 3, 4]


def test_build_schedule_timing_120bpm():
    schedule = build_schedule(PHRASE, 120, start_time_ms=0)
    assert [e.expected_time_ms for e in schedule] == [0, 500, 1000, 1500, 2000]
    assert all(e.duration_ms == 500 for e in schedule)


# --- bol -> finger ---------------------------------------------------------------------

def test_build_schedule_bol_to_finger_matches_config():
    all_bols = list(SYLLABLE_FINGER)
    schedule = build_schedule(all_bols, 90)
    for bol, expected in zip(all_bols, schedule):
        assert expected.finger == SYLLABLE_FINGER[bol]
        assert expected.finger in FINGERS


def test_build_schedule_unsupported_syllable_raises():
    with pytest.raises(UnsupportedSyllableError, match="boom"):
        build_schedule(["tha", "boom"], 90)


# --- TimingWindow validation -----------------------------------------------------------

def test_timing_window_defaults_are_valid():
    w = TimingWindow()
    assert w.on_time_ms == 120 and w.accept_ms == 300


def test_timing_window_rejects_negative_on_time():
    with pytest.raises(ValueError, match="on_time_ms"):
        TimingWindow(on_time_ms=-1)


def test_timing_window_rejects_non_positive_accept():
    with pytest.raises(ValueError, match="accept_ms"):
        TimingWindow(accept_ms=0)
    with pytest.raises(ValueError, match="accept_ms"):
        TimingWindow(accept_ms=-50)


def test_timing_window_rejects_on_time_greater_than_accept():
    with pytest.raises(ValueError, match="on_time_ms"):
        TimingWindow(on_time_ms=400, accept_ms=300)


# --- scoring: single expected/actual pair ----------------------------------------------

def _single_schedule(bol: str = "dhim", bpm: float = 60, start_time_ms: int = 1000) -> ExpectedEvent:
    return build_schedule([bol], bpm, start_time_ms=start_time_ms)[0]


def test_score_correct_on_time():
    exp = _single_schedule()
    result = score_events([exp], [InputEvent(exp.expected_time_ms + 100, exp.finger, "test")])[0]
    assert result.outcome == Outcome.CORRECT_ON_TIME
    assert result.timing_error_ms == 100
    assert result.expected is exp and result.actual is not None


def test_score_correct_early():
    exp = _single_schedule()
    result = score_events([exp], [InputEvent(exp.expected_time_ms - 200, exp.finger, "test")])[0]
    assert result.outcome == Outcome.CORRECT_EARLY
    assert result.timing_error_ms == -200


def test_score_correct_late():
    exp = _single_schedule()
    result = score_events([exp], [InputEvent(exp.expected_time_ms + 250, exp.finger, "test")])[0]
    assert result.outcome == Outcome.CORRECT_LATE
    assert result.timing_error_ms == 250


def test_score_wrong_finger_still_consumes_expected():
    exp = _single_schedule()  # finger == "thumb"
    results = score_events([exp], [InputEvent(exp.expected_time_ms + 50, "index", "test")])
    assert len(results) == 1
    assert results[0].outcome == Outcome.WRONG_FINGER
    assert results[0].timing_error_ms == 50
    assert results[0].expected is exp
    assert results[0].actual is not None


def test_score_missed():
    exp = _single_schedule()
    results = score_events([exp], [])
    assert len(results) == 1
    assert results[0].outcome == Outcome.MISSED
    assert results[0].expected is exp
    assert results[0].actual is None
    assert results[0].timing_error_ms is None


def test_score_extra():
    tap = InputEvent(9999, "thumb", "test")
    results = score_events([], [tap])
    assert len(results) == 1
    assert results[0].outcome == Outcome.EXTRA
    assert results[0].expected is None
    assert results[0].actual is tap
    assert results[0].timing_error_ms is None


# --- boundary values ---------------------------------------------------------------------

def test_score_boundary_on_time_exactly_120ms():
    exp = _single_schedule()
    late = score_events([exp], [InputEvent(exp.expected_time_ms + 120, exp.finger, "test")])[0]
    early = score_events([exp], [InputEvent(exp.expected_time_ms - 120, exp.finger, "test")])[0]
    assert late.outcome == Outcome.CORRECT_ON_TIME
    assert early.outcome == Outcome.CORRECT_ON_TIME


def test_score_boundary_accept_exactly_300ms():
    exp = _single_schedule()
    late = score_events([exp], [InputEvent(exp.expected_time_ms + 300, exp.finger, "test")])[0]
    early = score_events([exp], [InputEvent(exp.expected_time_ms - 300, exp.finger, "test")])[0]
    assert late.outcome == Outcome.CORRECT_LATE
    assert early.outcome == Outcome.CORRECT_EARLY


def test_score_boundary_outside_accept_window_is_missed_and_extra():
    exp = _single_schedule()
    results = score_events([exp], [InputEvent(exp.expected_time_ms + 301, exp.finger, "test")])
    outcomes = {r.outcome for r in results}
    assert outcomes == {Outcome.MISSED, Outcome.EXTRA}


# --- global nearest-pair-first matching (arrival-order regression) ----------------------

def test_score_competing_actuals_global_nearest_pair_wins():
    schedule = build_schedule(["dhim", "tha"], 120, start_time_ms=0)
    e1, e2 = schedule  # e1: thumb@0ms, e2: index@500ms
    a1 = InputEvent(290, e1.finger, "test")
    a2 = InputEvent(295, e2.finger, "test")

    # Naive arrival-order processing (a1 first) would give e1<-a2 e2<-a1; the correct
    # global-nearest-first pairing is e1<-a1 (delta 290) and e2<-a2 (delta -205, smaller
    # than e2<-a1's -210) — verify this holds regardless of the order events are passed in.
    for events in ([a1, a2], [a2, a1]):
        results = score_events(schedule, events)
        assert results[0].expected is e1 and results[0].actual.timestamp_ms == 290
        assert results[1].expected is e2 and results[1].actual.timestamp_ms == 295


# --- purity: the module must not touch the clock ----------------------------------------

def test_scheduler_module_never_imports_time():
    import asan.scheduler as scheduler_module

    assert "time" not in vars(scheduler_module)


# --- JSON-safe serialization --------------------------------------------------------------

def test_score_result_as_dict_outcome_is_plain_string():
    exp = _single_schedule()
    result = score_events([exp], [InputEvent(exp.expected_time_ms, exp.finger, "test")])[0]
    d = result.as_dict()
    assert d["outcome"] == "correct_on_time"
    assert type(d["outcome"]) is str
