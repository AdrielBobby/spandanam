from spandanam.config import DEFAULT_MAP, MOTORS
from spandanam.haptic import compose_frame


def test_frame_layout_and_routing():
    lv = {"bass": 1.0, "treble": 0.0, "horn": 0.0, "cymbal": 0.5}
    fb = compose_frame(lv, {b: False for b in lv}, DEFAULT_MAP, {b: 1.0 for b in lv}, None, 255)
    assert fb[0:1] == b"S" and len(fb) == 9
    vals = dict(zip(MOTORS, fb[1:9]))
    assert vals["chest"] == 255 and vals["l_finger"] == 127 and vals["l_wrist"] == 0


def test_gain_and_onset_kick_are_clamped():
    lv = {"bass": 0.9, "treble": 0, "horn": 0, "cymbal": 0}
    fb = compose_frame(lv, {"bass": True}, DEFAULT_MAP, {"bass": 1.5}, None, 255)
    assert fb[1] == 255


def test_motif_overlays_max():
    lv = {b: 0.0 for b in DEFAULT_MAP}
    fb = compose_frame(lv, {}, DEFAULT_MAP, {}, {"back": 200}, 255)
    assert dict(zip(MOTORS, fb[1:9]))["back"] == 200
