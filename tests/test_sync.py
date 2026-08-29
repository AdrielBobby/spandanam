from melam.sync import group_reference, haptic_cue, phase_offset_ms, tempo_from_strikes


def test_tempo_120bpm():
    ts = [i * 500_000 for i in range(10)]  # 500 ms IOI
    t = tempo_from_strikes("d1", ts)
    assert abs(t.bpm - 120) < 0.1 and t.jitter_ms == 0


def test_phase_offset_positive_when_late():
    ref = [i * 500_000 for i in range(10)]
    late = [t + 60_000 for t in ref]
    assert abs(phase_offset_ms(ref, late) - 60) < 0.01


def test_haptic_cue_mapping():
    assert haptic_cue(80, 40) == "F"
    assert haptic_cue(-80, 40) == "S"
    assert haptic_cue(10, 40) is None


def test_group_reference_prefers_asan():
    assert group_reference({"asan": [1, 2], "drummer-1": [1, 2, 3]}) == [1, 2]
    assert group_reference({"drummer-1": [1, 2, 3], "drummer-2": [1]}) == [1, 2, 3]
