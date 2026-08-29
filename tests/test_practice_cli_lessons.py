from asan.lessons import load_lesson
from asan.practice_cli import DEFAULT_LESSON_ID, build_lesson_schedule, parse_args


# --- parse_args ----------------------------------------------------------------------------

def test_parse_args_default_lesson_and_no_bpm():
    args = parse_args([])
    assert args.lesson == DEFAULT_LESSON_ID == "vaaythari_basic_1"
    assert args.bpm is None


def test_parse_args_lesson_and_bpm_override():
    args = parse_args(["--lesson", "vaaythari_inter_1", "--bpm", "100"])
    assert args.lesson == "vaaythari_inter_1"
    assert args.bpm == 100.0


# --- build_lesson_schedule -------------------------------------------------------------------

def test_build_lesson_schedule_uses_lesson_finger_map_not_global_config():
    # "ka" maps to "pinky" here, unlike config.SYLLABLE_FINGER's "ring" -- proves the
    # lesson's own finger_map is what drives the schedule, not the global config.
    phrase = ["dhim", "ka"]
    finger_map = {"dhim": "thumb", "ka": "pinky"}
    schedule = build_lesson_schedule(phrase, finger_map, tempo_bpm=60, start_time_ms=0)

    assert len(schedule) == 2
    assert schedule[0].bol == "dhim" and schedule[0].finger == "thumb"
    assert schedule[1].bol == "ka" and schedule[1].finger == "pinky"


def test_build_lesson_schedule_timing_matches_beat_duration():
    schedule = build_lesson_schedule(
        ["dhim", "tha", "ka"], {"dhim": "thumb", "tha": "index", "ka": "ring"}, tempo_bpm=60, start_time_ms=750
    )
    assert schedule[0].expected_time_ms == 750
    assert schedule[1].expected_time_ms == 750 + 1000  # 60 bpm -> 1000ms/beat
    assert schedule[2].expected_time_ms == 750 + 2000


# --- end-to-end smoke test (no console I/O) -------------------------------------------------

def test_smoke_default_lesson_loads_and_builds_schedule_without_error():
    args = parse_args(["--lesson", DEFAULT_LESSON_ID])
    lesson = load_lesson(args.lesson)
    tempo_bpm = args.bpm if args.bpm is not None else lesson["tempo_bpm"]

    schedule = build_lesson_schedule(lesson["phrase"], lesson["finger_map"], tempo_bpm, start_time_ms=750)

    assert len(schedule) == len(lesson["phrase"])
    assert all(e.finger in {"thumb", "index", "middle", "ring", "pinky"} for e in schedule)
