from melam.fatigue import extract


def test_amp_decay_and_hr_slope():
    strikes = [(i * 0.5, 6.0) for i in range(20)] + [(10 + i * 0.5, 3.0) for i in range(20)]
    hr = [(0, 100.0), (60, 120.0)]
    f = extract("d3", 30, hr, strikes)
    assert abs(f.amp_decay_pct - 50) < 0.1
    assert abs(f.hr_slope_bpm_per_min - 20) < 0.1
    assert f.hr_bpm == 110  # median of recent readings


def test_empty_is_safe():
    f = extract("d1", 30, [], [])
    assert f.hr_bpm == 0 and f.amp_decay_pct == 0 and f.jitter_growth_pct == 0
