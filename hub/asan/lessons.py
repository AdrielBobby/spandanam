"""Lesson content loader: JSON lesson files under content/lessons/ (phrase, finger
map, tempo, metadata) that practice_cli.py selects via --lesson, replacing the old
hardcoded PHRASE constant. Pure data loading + validation: no clock, keyboard, or
hardware access.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

VALID_FINGERS = {"thumb", "index", "middle", "ring", "pinky"}
VALID_LEVELS = {"beginner", "intermediate", "advanced"}

# repo_root/content/lessons/*.json
LESSONS_DIR = Path(__file__).resolve().parents[2] / "content" / "lessons"

_REQUIRED_FIELDS = {"id", "name", "level", "tempo_bpm", "phrase", "finger_map", "repeats", "focus"}


def _validate_lesson(lesson: dict[str, Any], source: Path) -> None:
    """Raise ValueError (with source path context) if lesson doesn't satisfy the schema."""
    missing = _REQUIRED_FIELDS - lesson.keys()
    if missing:
        raise ValueError(f"{source}: missing required field(s): {sorted(missing)}")

    if lesson["level"] not in VALID_LEVELS:
        raise ValueError(f"{source}: invalid level {lesson['level']!r}, must be one of {sorted(VALID_LEVELS)}")

    if not isinstance(lesson["tempo_bpm"], (int, float)) or isinstance(lesson["tempo_bpm"], bool) or lesson["tempo_bpm"] <= 0:
        raise ValueError(f"{source}: tempo_bpm must be a number > 0, got {lesson['tempo_bpm']!r}")

    if not isinstance(lesson["repeats"], int) or isinstance(lesson["repeats"], bool) or lesson["repeats"] < 1:
        raise ValueError(f"{source}: repeats must be an integer >= 1, got {lesson['repeats']!r}")

    if not lesson["phrase"]:
        raise ValueError(f"{source}: phrase must be a non-empty list of bols")

    finger_map = lesson["finger_map"]
    missing_bols = sorted({bol for bol in lesson["phrase"] if bol not in finger_map})
    if missing_bols:
        raise ValueError(f"{source}: phrase bol(s) missing from finger_map: {missing_bols}")

    invalid_fingers = sorted({f for f in finger_map.values() if f not in VALID_FINGERS})
    if invalid_fingers:
        raise ValueError(
            f"{source}: invalid finger(s) in finger_map: {invalid_fingers}, must be one of {sorted(VALID_FINGERS)}"
        )


def _load_all(lessons_dir: Path) -> dict[str, dict[str, Any]]:
    """Load and validate every *.json file in lessons_dir, keyed by lesson id. Raises
    ValueError on the first invalid lesson file encountered, or on a duplicate id."""
    lessons: dict[str, dict[str, Any]] = {}
    for path in sorted(lessons_dir.glob("*.json")):
        with path.open("r", encoding="utf-8") as f:
            lesson = json.load(f)
        _validate_lesson(lesson, path)
        lesson_id = lesson["id"]
        if lesson_id in lessons:
            raise ValueError(f"{path}: duplicate lesson id {lesson_id!r} (already defined in another file)")
        lessons[lesson_id] = lesson
    return lessons


def list_lessons(lessons_dir: Path = LESSONS_DIR) -> list[dict[str, str]]:
    """Metadata (id, name, level) for every lesson in lessons_dir, sorted by id."""
    lessons = _load_all(lessons_dir)
    return [
        {"id": lesson["id"], "name": lesson["name"], "level": lesson["level"]}
        for lesson in sorted(lessons.values(), key=lambda l: l["id"])
    ]


def load_lesson(lesson_id: str, lessons_dir: Path = LESSONS_DIR) -> dict[str, Any]:
    """Full lesson dict for lesson_id. Raises ValueError if no lesson with that id
    exists in lessons_dir, or if any lesson file in lessons_dir is invalid."""
    lessons = _load_all(lessons_dir)
    if lesson_id not in lessons:
        raise ValueError(f"unknown lesson id {lesson_id!r}; available: {sorted(lessons.keys())}")
    return lessons[lesson_id]
