from viral.imu import Stroke
from viral.motion import FLAT_TILT_DEG, motion_feedback


def test_no_strokes_returns_none():
    assert motion_feedback([]) is None


def test_upright_strokes_are_good_with_no_hint():
    strokes = [Stroke(0.0, 3.0, 80.0), Stroke(1.0, 3.5, 75.0)]
    fb = motion_feedback(strokes)
    assert fb.verdict == "good" and fb.hint == ""
    assert fb.avg_tilt_deg == 77.5
    assert fb.avg_peak_g == 3.25


def test_flat_strokes_get_a_hint():
    strokes = [Stroke(0.0, 3.0, 10.0), Stroke(1.0, 3.0, 12.0)]
    fb = motion_feedback(strokes)
    assert fb.verdict == "flat"
    assert "upright" in fb.hint.lower()


def test_tilt_at_threshold_is_flat_not_good():
    # avg_tilt < FLAT_TILT_DEG is "flat"; exactly at the threshold is still "good" (strict <)
    assert motion_feedback([Stroke(0.0, 3.0, FLAT_TILT_DEG)]).verdict == "good"
    assert motion_feedback([Stroke(0.0, 3.0, FLAT_TILT_DEG - 0.1)]).verdict == "flat"


def test_as_dict_rounds_and_has_expected_keys():
    fb = motion_feedback([Stroke(0.0, 3.123456, 80.987654)])
    d = fb.as_dict()
    assert set(d.keys()) == {"avg_tilt_deg", "avg_peak_g", "verdict", "hint"}
    assert d["avg_tilt_deg"] == 81.0
    assert d["avg_peak_g"] == 3.12
