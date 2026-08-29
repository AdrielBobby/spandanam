from viral import judge
from viral.events import Strike
from viral.score import Note, Score


def _score():
    return Score("t", 120, 4, (Note(0, 0), Note(1, 1), Note(2, 2)))   # beat = 0.5 s


def test_perfect_good_late_wrong_and_extra():
    sc = _score(); st = judge.PlayState(start_s=100.0)
    st, j = judge.judge_strike(sc, st, Strike(0, 100.02, 1, "key")); assert j.verdict == "perfect" and st.points == 100
    st, j = judge.judge_strike(sc, st, Strike(1, 100.57, 1, "key")); assert j.verdict == "good" and st.streak == 2
    st, j = judge.judge_strike(sc, st, Strike(3, 101.0, 1, "key")); assert j.verdict == "wrong_finger" and st.streak == 0
    st, j = judge.judge_strike(sc, st, Strike(2, 105.0, 1, "key")); assert j.verdict == "extra"


def test_sweep_misses_and_summary():
    sc = _score(); st = judge.PlayState(start_s=100.0)
    st, missed = judge.sweep_misses(sc, st, 100.3); assert missed == [0] and st.misses == 1
    st, missed = judge.sweep_misses(sc, st, 100.3); assert missed == []
    s = judge.summary(sc, st); assert s["misses"] == 1 and s["stars"] == 0


def test_upcoming_window():
    sc = _score(); st = judge.PlayState(start_s=100.0)
    assert judge.upcoming(sc, st, 100.42, 0.12) == [1]
