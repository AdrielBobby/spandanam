from asan.vaaythari import Phrase, diff_phrase, tap_schedule, validate_syllables


def test_tap_schedule_hands_and_accent():
    p = Phrase(("dhim", "tha", "ka"), 120)
    taps = tap_schedule(p)
    zones = [(round(t.t_s, 2), t.zone) for t in taps]
    assert (0.0, "right") in zones and (0.0, "accent") in zones
    assert (0.5, "right") in zones and (1.0, "left") in zones
    assert p.duration_s == 1.5


def test_diff_missing_extra_swapped():
    d = diff_phrase(("tha", "ki", "ta"), ("tha", "ka", "ta", "ta"))
    assert d.swapped == (("ki", "ka"),) and d.extra == ("ta",) and d.missing == ()
    assert diff_phrase(("tha", "ki", "ta"), ("tha", "ki", "ta")).similarity == 1.0


def test_validate_drops_unknown():
    assert validate_syllables(["tha", "boom", "ka"]) == ("tha", "ka")
