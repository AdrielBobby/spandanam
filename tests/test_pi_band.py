from spandanam.config import MOTORS
from spandanam.pi_band import collapse_to_zones
from spandanam.tap_sync import detect_tap, tap_sync


def test_collapse_max_pools_into_three_zones():
    vals = {m: 0 for m in MOTORS}; vals["back"] = 255; vals["r_wrist"] = 128; vals["l_finger"] = 64
    frame = b"S" + bytes(vals[m] for m in MOTORS)
    z = collapse_to_zones(frame)
    assert z["chest"] == 1.0 and abs(z["wrist"] - 128 / 255) < 1e-6 and abs(z["finger"] - 64 / 255) < 1e-6


def test_tap_sync_locked_and_late():
    onsets = [i * 0.5 for i in range(10)]
    assert tap_sync(onsets, [o + 0.03 for o in onsets]).locked
    s = tap_sync(onsets, [o + 0.2 for o in onsets])
    assert not s.locked and s.offset_ms > 150


def test_detect_tap_rise():
    assert detect_tap(1.0, 4.0) and not detect_tap(1.0, 1.5)
