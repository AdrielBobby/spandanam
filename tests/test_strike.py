from melam.strike import StrikeState, detect_strike


def test_detects_single_strike_and_rearms():
    st = StrikeState()
    st, hit = detect_strike(st, 0, 1.0, 3.0, 0.08)
    assert hit is None
    st, hit = detect_strike(st, 1000, 5.0, 3.0, 0.08)
    assert hit is not None and hit.peak_g == 4.0
    # still high: no double count
    st, hit = detect_strike(st, 2000, 5.0, 3.0, 0.08)
    assert hit is None
    # drop below half threshold -> re-arm
    st, hit = detect_strike(st, 3000, 1.2, 3.0, 0.08)
    assert st.armed and hit is None


def test_refractory_blocks_fast_double():
    st = StrikeState()
    st, h1 = detect_strike(st, 0, 6.0, 3.0, 0.08)
    st, _ = detect_strike(st, 10_000, 1.0, 3.0, 0.08)     # re-arm
    st, h2 = detect_strike(st, 20_000, 6.0, 3.0, 0.08)    # 20 ms later < 80 ms
    assert h1 and h2 is None
