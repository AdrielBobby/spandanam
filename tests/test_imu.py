from asan.imu import stroke_from_samples


def test_stroke_needs_sharp_rise():
    assert stroke_from_samples(1.0, [1.0, 1.1], (0, 0, 1), 2.5) is None
    s = stroke_from_samples(1.0, [1.0, 5.0], (0, 0.7, 0.7), 2.5)
    assert s and abs(s.peak_g - 4.0) < 1e-6 and 40 < s.tilt_deg < 50


def test_write_window_csv(tmp_path):
    from viral.imu_record import write_window
    win = ((1.000, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0), (1.004, 0.1, 0.0, 3.2, 12.0, -3.0, 0.5))
    n = write_window(tmp_path / "index" / "index.0001.csv", win)
    rows = (tmp_path / "index" / "index.0001.csv").read_text().splitlines()
    assert n == 2 and rows[0] == "timestamp,ax,ay,az,gx,gy,gz" and rows[2].startswith("4.0,0.1,0.0,3.2,12.0,-3.0,0.5")


def test_stroke_has_window_field():
    from viral.imu import Stroke, PRE_S, POST_S
    s = Stroke(1.0, 2.0, 5.0); assert s.window == () and PRE_S < POST_S
