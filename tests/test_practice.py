import pytest

from asan.config import FINGERS
from asan.input_sources import KEY_FINGER_MAP, InputEvent
from asan.practice import (
    FINGER_KEY_MAP,
    Summary,
    collection_window_ms,
    cue_time_ms,
    format_cue,
    format_prepare_cue,
    format_result_table,
    summarize,
    to_relative_event,
)
from asan.scheduler import ExpectedEvent, Outcome, ScoreResult, TimingWindow, build_schedule, score_events

PHRASE = ["dhim", "tha", "ka", "ta", "ki"]


# --- collection_window_ms ---------------------------------------------------------------

def test_collection_window_ms_uses_last_beat_plus_accept_plus_tail():
    schedule = build_schedule(PHRASE, 90, start_time_ms=0)
    window = TimingWindow(on_time_ms=120, accept_ms=300)
    last_expected_ms = schedule[-1].expected_time_ms
    assert collection_window_ms(schedule, window, tail_ms=500) == last_expected_ms + 300 + 500
    assert collection_window_ms(schedule, window, tail_ms=0) == last_expected_ms + 300


def test_collection_window_ms_rejects_empty_schedule():
    with pytest.raises(ValueError, match="non-empty schedule"):
        collection_window_ms((), TimingWindow())


# --- to_relative_event -------------------------------------------------------------------

def test_to_relative_event_shifts_timestamp_only():
    event = InputEvent(1500, "ring", "keyboard_simulator", 0.7)
    relative = to_relative_event(event, start_time_ms=1000)
    assert relative.timestamp_ms == 500


def test_to_relative_event_preserves_finger_source_strength_exactly():
    event = InputEvent(2345, "pinky", "keyboard_simulator", 1.0)
    relative = to_relative_event(event, start_time_ms=345)
    assert relative.finger == event.finger == "pinky"
    assert relative.source == event.source == "keyboard_simulator"
    assert relative.strength == event.strength == 1.0


def test_to_relative_event_can_produce_negative_timestamp():
    event = InputEvent(100, "thumb", "keyboard_simulator", 1.0)
    relative = to_relative_event(event, start_time_ms=1000)
    assert relative.timestamp_ms == -900


# --- summarize -----------------------------------------------------------------------------

def test_summarize_no_expected_events_has_zero_accuracy():
    tap = InputEvent(9999, "thumb", "test")
    results = score_events((), [tap])  # nothing expected, one extra tap
    summary = summarize(results)
    assert summary.total_expected == 0
    assert summary.extra == 1
    assert summary.accepted_accuracy_pct == 0.0


def test_summarize_no_results_at_all_has_zero_accuracy():
    summary = summarize(())
    assert summary == Summary(0, 0, 0, 0, 0, 0, 0, 0.0)


def test_summarize_counts_are_internally_consistent():
    schedule = build_schedule(PHRASE, 90, start_time_ms=0)
    events = [
        InputEvent(schedule[0].expected_time_ms + 10, schedule[0].finger, "test"),   # on_time
        InputEvent(schedule[1].expected_time_ms - 200, schedule[1].finger, "test"),  # early
        InputEvent(schedule[2].expected_time_ms + 250, schedule[2].finger, "test"),  # late
        InputEvent(schedule[3].expected_time_ms, "pinky", "test"),                    # wrong_finger (expected middle)
        # schedule[4] gets nothing -> missed
        InputEvent(50_000, "thumb", "test"),                                          # extra
    ]
    results = score_events(schedule, events)
    summary = summarize(results)

    assert summary.correct_on_time == 1
    assert summary.correct_early == 1
    assert summary.correct_late == 1
    assert summary.wrong_finger == 1
    assert summary.missed == 1
    assert summary.extra == 1
    assert summary.total_expected == len(schedule) == 5
    assert (
        summary.correct_on_time + summary.correct_early + summary.correct_late
        + summary.wrong_finger + summary.missed
    ) == summary.total_expected
    assert len(results) == summary.total_expected + summary.extra
    assert summary.accepted_accuracy_pct == pytest.approx(3 / 5 * 100)


def test_summarize_all_correct_is_100_percent_accuracy():
    schedule = build_schedule(["dhim", "tha"], 60, start_time_ms=0)
    events = [InputEvent(e.expected_time_ms, e.finger, "test") for e in schedule]
    summary = summarize(score_events(schedule, events))
    assert summary.accepted_accuracy_pct == 100.0


# --- FINGER_KEY_MAP / format_cue ----------------------------------------------------------

def test_finger_key_map_is_inverse_of_key_finger_map():
    assert len(FINGER_KEY_MAP) == len(KEY_FINGER_MAP) == len(FINGERS)
    for key, finger in KEY_FINGER_MAP.items():
        assert FINGER_KEY_MAP[finger] == key


def test_format_cue_matches_hit_now_format():
    schedule = build_schedule(["dhim", "tha", "ka", "ta", "ki"], 90, start_time_ms=0)
    assert format_cue(schedule[0]) == ">>> HIT NOW -> THUMB  [1]  dhim"
    assert format_cue(schedule[1]) == ">>> HIT NOW -> INDEX  [2]  tha"
    assert format_cue(schedule[2]) == ">>> HIT NOW -> RING   [4]  ka"
    assert format_cue(schedule[3]) == ">>> HIT NOW -> MIDDLE [3]  ta"
    assert format_cue(schedule[4]) == ">>> HIT NOW -> RING   [4]  ki"


def test_format_cue_rejects_finger_not_in_map():
    bad_event = ExpectedEvent(beat_index=0, bol="dhim", finger="sixth_finger", expected_time_ms=0, duration_ms=1000)
    with pytest.raises(ValueError, match="sixth_finger"):
        format_cue(bad_event)


def test_format_prepare_cue_matches_format():
    schedule = build_schedule(["dhim", "tha", "ka", "ta", "ki"], 90, start_time_ms=0)
    assert format_prepare_cue(schedule[0]) == "PREPARE -> THUMB  [1]  dhim"
    assert format_prepare_cue(schedule[1]) == "PREPARE -> INDEX  [2]  tha"
    assert format_prepare_cue(schedule[2]) == "PREPARE -> RING   [4]  ka"
    assert format_prepare_cue(schedule[3]) == "PREPARE -> MIDDLE [3]  ta"
    assert format_prepare_cue(schedule[4]) == "PREPARE -> RING   [4]  ki"


def test_format_prepare_cue_rejects_finger_not_in_map():
    bad_event = ExpectedEvent(beat_index=0, bol="dhim", finger="sixth_finger", expected_time_ms=0, duration_ms=1000)
    with pytest.raises(ValueError, match="sixth_finger"):
        format_prepare_cue(bad_event)


# --- cue_time_ms -----------------------------------------------------------------------------

def test_cue_time_ms_subtracts_advance():
    event = ExpectedEvent(beat_index=0, bol="dhim", finger="thumb", expected_time_ms=1000, duration_ms=1333)
    assert cue_time_ms(event, 450) == 550


def test_cue_time_ms_never_negative():
    event = ExpectedEvent(beat_index=0, bol="dhim", finger="thumb", expected_time_ms=100, duration_ms=1333)
    assert cue_time_ms(event, 450) == 0


def test_cue_time_ms_equals_expected_when_advance_zero():
    event = ExpectedEvent(beat_index=0, bol="dhim", finger="thumb", expected_time_ms=1000, duration_ms=1333)
    assert cue_time_ms(event, 0) == event.expected_time_ms == 1000


def test_cue_time_ms_rejects_negative_advance():
    event = ExpectedEvent(beat_index=0, bol="dhim", finger="thumb", expected_time_ms=1000, duration_ms=1333)
    with pytest.raises(ValueError, match="cue_advance_ms"):
        cue_time_ms(event, -1)


# --- format_result_table ------------------------------------------------------------------

def test_format_result_table_has_header_and_one_row_per_result():
    schedule = build_schedule(["dhim", "tha"], 60, start_time_ms=0)
    events = [InputEvent(schedule[0].expected_time_ms, schedule[0].finger, "test")]
    results = score_events(schedule, events)  # 1 matched + 1 missed
    table = format_result_table(results)
    lines = table.splitlines()
    assert lines[0].startswith("beat")
    assert len(lines) == 1 + len(results)


def test_format_result_table_uses_dash_for_missing_expected_or_actual():
    result = ScoreResult(None, InputEvent(1234, "thumb", "test"), Outcome.EXTRA, None)
    table = format_result_table([result])
    row = table.splitlines()[1]
    assert row.split()[0] == "-"  # beat column blank for an extra tap with no expected event
