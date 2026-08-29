from asan.imu import stroke_from_samples


def test_stroke_needs_sharp_rise():
    assert stroke_from_samples(1.0, [1.0, 1.1], (0, 0, 1), 2.5) is None
    s = stroke_from_samples(1.0, [1.0, 5.0], (0, 0.7, 0.7), 2.5)
    assert s and abs(s.peak_g - 4.0) < 1e-6 and 40 < s.tilt_deg < 50
