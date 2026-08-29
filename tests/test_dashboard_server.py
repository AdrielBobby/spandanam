import json

import pytest

from dashboard.server import get_session_rounds, get_sessions, get_stats


def _write_jsonl(path, entries):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for e in entries:
            f.write(json.dumps(e) + "\n")


def _entry(session_id, tempo_bpm, accuracy_pct, weak_fingers, weak_bols):
    return {
        "timestamp": f"{session_id}T10:00:00+00:00",
        "session_id": session_id,
        "phrase": ["dhim", "tha", "ka"],
        "tempo_bpm": tempo_bpm,
        "summary": {
            "total_expected": 3,
            "correct_on_time": 2,
            "correct_early": 0,
            "correct_late": 0,
            "wrong_finger": 1,
            "missed": 0,
            "extra": 0,
            "accepted_accuracy_pct": accuracy_pct,
            "dominant_error": "wrong_finger",
            "weak_fingers": weak_fingers,
            "weak_bols": weak_bols,
            "recommended_tempo_bpm": tempo_bpm,
            "recommended_phrase": ["ka"],
        },
        "beats": [],
    }


@pytest.fixture
def log_path(tmp_path):
    path = tmp_path / "practice.jsonl"
    entries = [
        _entry("2026-08-27", 80, 60.0, ["ring"], ["ka"]),
        _entry("2026-08-27", 85, 80.0, ["ring"], ["ka"]),
        _entry("2026-08-28", 90, 100.0, [], []),
    ]
    _write_jsonl(path, entries)
    return path


def test_get_sessions_returns_unique_sorted_ids(log_path):
    assert get_sessions(log_path) == ["2026-08-27", "2026-08-28"]


def test_get_session_rounds_filters_by_session(log_path):
    rounds = get_session_rounds("2026-08-27", log_path)
    assert len(rounds) == 2
    assert all(r["session_id"] == "2026-08-27" for r in rounds)


def test_get_session_rounds_unknown_session_returns_empty(log_path):
    assert get_session_rounds("2099-01-01", log_path) == []


def test_get_stats_aggregates_correctly(log_path):
    stats = get_stats(log_path)
    assert stats["total_rounds"] == 3
    assert stats["avg_accuracy_pct"] == pytest.approx((60.0 + 80.0 + 100.0) / 3)
    assert stats["tempo_progression"] == [
        {"round": 1, "tempo_bpm": 80, "accuracy_pct": 60.0},
        {"round": 2, "tempo_bpm": 85, "accuracy_pct": 80.0},
        {"round": 3, "tempo_bpm": 90, "accuracy_pct": 100.0},
    ]
    assert stats["weak_fingers_freq"] == {"ring": 2}
    assert stats["weak_bols_freq"] == {"ka": 2}


def test_get_stats_empty_log_returns_zeros(tmp_path):
    stats = get_stats(tmp_path / "missing.jsonl")
    assert stats == {
        "total_rounds": 0,
        "avg_accuracy_pct": 0.0,
        "tempo_progression": [],
        "weak_fingers_freq": {},
        "weak_bols_freq": {},
    }
