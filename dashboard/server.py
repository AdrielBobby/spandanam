"""Minimal read-only dashboard API over the practice log written by
hub/asan/practice_cli.py (see LOG_PATH there). Deliberately standalone: no import of
the asan package, so the CLI can log and the dashboard can read without either one
depending on the other's runtime environment.
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException

LOG_PATH = Path(__file__).resolve().parent.parent / "logs" / "practice.jsonl"

app = FastAPI(title="Vaaythari Practice Dashboard")


def read_entries(path: Path = LOG_PATH) -> list[dict[str, Any]]:
    """Parse every JSON line in path, in file order. Returns [] if the file doesn't
    exist yet (no rounds logged) or is empty."""
    if not path.exists():
        return []
    entries = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                entries.append(json.loads(line))
    return entries


def get_sessions(path: Path = LOG_PATH) -> list[str]:
    """Unique session_id values, sorted ascending."""
    return sorted({e["session_id"] for e in read_entries(path)})


def get_session_rounds(session_id: str, path: Path = LOG_PATH) -> list[dict[str, Any]]:
    """All round entries for one session_id, in log order."""
    return [e for e in read_entries(path) if e["session_id"] == session_id]


def get_stats(path: Path = LOG_PATH) -> dict[str, Any]:
    """Aggregate stats across every logged round."""
    entries = read_entries(path)
    total_rounds = len(entries)

    if total_rounds == 0:
        return {
            "total_rounds": 0,
            "avg_accuracy_pct": 0.0,
            "tempo_progression": [],
            "weak_fingers_freq": {},
            "weak_bols_freq": {},
        }

    accuracies = [e["summary"]["accepted_accuracy_pct"] for e in entries]
    avg_accuracy_pct = sum(accuracies) / total_rounds

    tempo_progression = [
        {
            "round": i + 1,
            "tempo_bpm": e["tempo_bpm"],
            "accuracy_pct": e["summary"]["accepted_accuracy_pct"],
        }
        for i, e in enumerate(entries)
    ]

    weak_fingers_freq: Counter[str] = Counter()
    weak_bols_freq: Counter[str] = Counter()
    for e in entries:
        weak_fingers_freq.update(e["summary"]["weak_fingers"])
        weak_bols_freq.update(e["summary"]["weak_bols"])

    return {
        "total_rounds": total_rounds,
        "avg_accuracy_pct": avg_accuracy_pct,
        "tempo_progression": tempo_progression,
        "weak_fingers_freq": dict(weak_fingers_freq),
        "weak_bols_freq": dict(weak_bols_freq),
    }


@app.get("/sessions")
def list_sessions() -> list[str]:
    return get_sessions()


@app.get("/sessions/{session_id}")
def session_detail(session_id: str) -> list[dict[str, Any]]:
    rounds = get_session_rounds(session_id)
    if not rounds:
        raise HTTPException(status_code=404, detail=f"no rounds logged for session_id={session_id!r}")
    return rounds


@app.get("/stats")
def stats() -> dict[str, Any]:
    return get_stats()
