import logging
import time

from viral.hardware import Glove, _name
from viral.imu import MPU6050Reader, Stroke


def test_name_maps_index_to_finger():
    assert _name(0) == "thumb"
    assert _name(4) == "pinky"


def test_name_out_of_range_falls_back():
    assert _name(9) == "f9"
    assert _name(-1) == "f-1"


def test_glove_dry_constructs_without_gpiozero():
    # gpiozero/smbus2 are not installed on the laptop; dry mode must never import them.
    g = Glove(dry=True)
    assert g.dry is True


def test_cue_logs_finger_name_in_dry_mode(caplog):
    g = Glove(dry=True)
    with caplog.at_level(logging.INFO, logger="viral.hardware"):
        g.cue(0, ms=25, led=True)
    assert "cue thumb 25ms x1.00 led=on" in caplog.text


def test_led_and_all_off_log_in_dry_mode(caplog):
    g = Glove(dry=True)
    with caplog.at_level(logging.INFO, logger="viral.hardware"):
        g.led(1, True)
        g.all_off()
    assert "led index on" in caplog.text
    assert "all_off" in caplog.text


def test_cue_is_non_blocking_in_dry_mode():
    g = Glove(dry=True)
    t0 = time.monotonic()
    g.cue(0, ms=5000)
    assert time.monotonic() - t0 < 0.1


def test_reader_dry_run_drains_empty():
    r = MPU6050Reader(threshold_g=2.5, dry_run=True)
    r.start()
    r.join(0.05)
    assert r.drain() == []


def test_drain_returns_then_clears():
    r = MPU6050Reader(threshold_g=2.5, dry_run=True)
    r._strokes.extend([Stroke(0.1, 3.0, 10.0), Stroke(0.2, 4.0, 12.0)])
    assert len(r.drain()) == 2
    assert r.drain() == []
