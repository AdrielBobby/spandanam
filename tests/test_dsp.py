import numpy as np
from spandanam.dsp import band_energies, detect_onsets, normalise


def _tone(f, sr=16000, n=160):
    return np.sin(2 * np.pi * f * np.arange(n) / sr).astype(np.float32)


def test_bass_tone_lands_in_bass_band():
    e = band_energies(_tone(120), 16000)
    assert e["bass"] > e["treble"] and e["bass"] > e["cymbal"]


def test_cymbal_tone_lands_in_cymbal_band():
    e = band_energies(_tone(5000), 16000)
    assert e["cymbal"] > e["bass"]


def test_normalise_bounded_and_adaptive():
    lv, mx = normalise({"bass": 2.0, "treble": 0.5}, {})
    assert lv["bass"] == 1.0 and 0 < lv["treble"] <= 1.0
    lv2, _ = normalise({"bass": 1.0, "treble": 0.5}, mx)
    assert lv2["bass"] < 1.0


def test_onset_on_sharp_rise_only():
    on = detect_onsets({"bass": 0.9, "treble": 0.3}, {"bass": 0.2, "treble": 0.25})
    assert on["bass"] and not on["treble"]


def test_empty_frame_safe():
    assert all(v == 0.0 for v in band_energies(np.array([]), 16000).values())
