import json

import pytest

from asan.lessons import LESSONS_DIR, list_lessons, load_lesson

BASIC_1 = "vaaythari_basic_1"


def _write_lesson(path, **overrides):
    lesson = {
        "id": "test_lesson",
        "name": "Test Lesson",
        "level": "beginner",
        "tempo_bpm": 60,
        "phrase": ["dhim", "tha"],
        "finger_map": {"dhim": "thumb", "tha": "index"},
        "repeats": 2,
        "focus": "accuracy",
    }
    lesson.update(overrides)
    path.write_text(json.dumps(lesson), encoding="utf-8")
    return lesson


# --- list_lessons / load_lesson against the real content/lessons/ dir --------------------

def test_list_lessons_returns_all_shipped_lessons():
    lessons = list_lessons()
    ids = {l["id"] for l in lessons}
    assert ids == {"vaaythari_basic_1", "vaaythari_basic_2", "vaaythari_inter_1"}
    assert all(set(l.keys()) == {"id", "name", "level"} for l in lessons)
    assert [l["id"] for l in lessons] == sorted(ids)  # sorted by id


def test_load_lesson_known_id_matches_sample_file():
    lesson = load_lesson(BASIC_1)
    on_disk = json.loads((LESSONS_DIR / f"{BASIC_1}.json").read_text(encoding="utf-8"))
    assert lesson == on_disk
    assert lesson["phrase"] == ["dhim", "tha", "ka", "ta", "ki"]
    assert lesson["finger_map"]["dhim"] == "thumb"
    assert "pinky" not in lesson["finger_map"].values()


def test_load_lesson_unknown_id_raises_with_id_in_message():
    with pytest.raises(ValueError, match="nonexistent_lesson"):
        load_lesson("nonexistent_lesson")


# --- invalid lessons (each in its own tmp_path dir) ---------------------------------------

def test_missing_finger_map_entry_raises(tmp_path):
    _write_lesson(tmp_path / "bad.json", finger_map={"dhim": "thumb"})  # "tha" missing
    with pytest.raises(ValueError, match="finger_map"):
        load_lesson("test_lesson", tmp_path)


def test_invalid_finger_name_raises(tmp_path):
    _write_lesson(tmp_path / "bad.json", finger_map={"dhim": "thumb", "tha": "sixth_finger"})
    with pytest.raises(ValueError, match="sixth_finger"):
        load_lesson("test_lesson", tmp_path)


def test_tempo_bpm_zero_raises(tmp_path):
    _write_lesson(tmp_path / "bad.json", tempo_bpm=0)
    with pytest.raises(ValueError, match="tempo_bpm"):
        load_lesson("test_lesson", tmp_path)


def test_tempo_bpm_negative_raises(tmp_path):
    _write_lesson(tmp_path / "bad.json", tempo_bpm=-10)
    with pytest.raises(ValueError, match="tempo_bpm"):
        load_lesson("test_lesson", tmp_path)


def test_repeats_zero_raises(tmp_path):
    _write_lesson(tmp_path / "bad.json", repeats=0)
    with pytest.raises(ValueError, match="repeats"):
        load_lesson("test_lesson", tmp_path)


def test_invalid_level_raises(tmp_path):
    _write_lesson(tmp_path / "bad.json", level="expert")
    with pytest.raises(ValueError, match="level"):
        load_lesson("test_lesson", tmp_path)


def test_empty_phrase_raises(tmp_path):
    _write_lesson(tmp_path / "bad.json", phrase=[])
    with pytest.raises(ValueError, match="phrase"):
        load_lesson("test_lesson", tmp_path)


def test_missing_required_field_raises(tmp_path):
    lesson = {
        "id": "test_lesson", "name": "Test", "level": "beginner", "tempo_bpm": 60,
        "phrase": ["dhim"], "finger_map": {"dhim": "thumb"}, "repeats": 1,
        # "focus" omitted
    }
    (tmp_path / "bad.json").write_text(json.dumps(lesson), encoding="utf-8")
    with pytest.raises(ValueError, match="focus"):
        load_lesson("test_lesson", tmp_path)


def test_duplicate_lesson_id_across_files_raises(tmp_path):
    _write_lesson(tmp_path / "one.json")
    _write_lesson(tmp_path / "two.json")
    with pytest.raises(ValueError, match="duplicate"):
        load_lesson("test_lesson", tmp_path)
