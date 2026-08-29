from asan.analysis import analyze
from asan.input_sources import InputEvent
from asan.practice_cli import build_log_entry
from asan.scheduler import build_schedule, score_events

PHRASE = ["dhim", "tha", "ka", "ta", "ki"]


def test_build_log_entry_structure_and_beats_length():
    schedule = build_schedule(PHRASE, 90)
    events = [InputEvent(e.expected_time_ms, e.finger, "test") for e in schedule]
    results = score_events(schedule, events)
    analysis = analyze(results, PHRASE, current_tempo_bpm=90)

    entry = build_log_entry(results, PHRASE, 90.0, analysis)

    assert set(entry.keys()) == {"timestamp", "session_id", "phrase", "tempo_bpm", "summary", "beats"}
    assert entry["phrase"] == PHRASE
    assert entry["tempo_bpm"] == 90.0
    assert entry["session_id"] == entry["timestamp"][:10]
    assert len(entry["beats"]) == len(schedule) == 5

    summary = entry["summary"]
    expected_summary_keys = {
        "total_expected", "correct_on_time", "correct_early", "correct_late",
        "wrong_finger", "missed", "extra", "accepted_accuracy_pct",
        "dominant_error", "weak_fingers", "weak_bols",
        "recommended_tempo_bpm", "recommended_phrase",
    }
    assert set(summary.keys()) == expected_summary_keys
    assert summary["accepted_accuracy_pct"] == 100.0

    beat = entry["beats"][0]
    assert set(beat.keys()) == {
        "index", "bol", "expected_finger", "expected_ms",
        "actual_finger", "actual_ms", "error_ms", "outcome",
    }
    assert beat["bol"] == "dhim"
    assert beat["outcome"] == "correct_on_time"


def test_build_log_entry_missed_beat_has_null_actual():
    schedule = build_schedule(PHRASE, 90)
    events = [InputEvent(e.expected_time_ms, e.finger, "test") for e in schedule[:-1]]  # last beat missed
    results = score_events(schedule, events)
    analysis = analyze(results, PHRASE, current_tempo_bpm=90)

    entry = build_log_entry(results, PHRASE, 90.0, analysis)
    missed_beat = entry["beats"][-1]
    assert missed_beat["outcome"] == "missed"
    assert missed_beat["actual_finger"] is None
    assert missed_beat["actual_ms"] is None
    assert missed_beat["error_ms"] is None


def test_build_log_entry_extra_tap_excluded_from_beats():
    schedule = build_schedule(["dhim", "tha"], 60)
    events = [
        InputEvent(schedule[0].expected_time_ms, schedule[0].finger, "test"),
        InputEvent(schedule[1].expected_time_ms, schedule[1].finger, "test"),
        InputEvent(50_000, "thumb", "test"),  # extra, no matching expected beat
    ]
    results = score_events(schedule, events)
    analysis = analyze(results, ["dhim", "tha"], current_tempo_bpm=60)

    entry = build_log_entry(results, ["dhim", "tha"], 60.0, analysis)
    assert entry["summary"]["extra"] == 1
    assert len(entry["beats"]) == 2  # extra tap not represented as a beat
