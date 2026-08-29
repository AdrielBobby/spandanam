"""Real-time hit judging (Yousician-style). Pure functions over an immutable state."""
from __future__ import annotations

from dataclasses import dataclass, replace

from .config import GOOD_MS, MISS_MS, PERFECT_MS
from .events import Strike
from .score import Score


@dataclass(frozen=True)
class Judgement:
    note_index: int | None
    verdict: str            # perfect | good | late | early | wrong_finger | miss | extra
    offset_ms: float
    finger: int


@dataclass(frozen=True)
class PlayState:
    start_s: float
    hit: frozenset[int] = frozenset()
    streak: int = 0
    points: int = 0
    perfect: int = 0
    good: int = 0
    misses: int = 0
    wrong: int = 0
    extra: int = 0
    log: tuple = ()          # (note_index|None, verdict, offset_ms, finger) per strike / miss


def note_time_s(score: Score, idx: int, start_s: float) -> float:
    return start_s + score.notes[idx].beat * score.beat_s


def judge_strike(score: Score, st: PlayState, s: Strike) -> tuple[PlayState, Judgement]:
    """Find the nearest un-hit note within MISS_MS; grade by |offset| and finger."""
    best, best_off = None, None
    for i, n in enumerate(score.notes):
        if i in st.hit:
            continue
        off = (s.t_s - note_time_s(score, i, st.start_s)) * 1000
        if abs(off) <= MISS_MS and (best_off is None or abs(off) < abs(best_off)):
            best, best_off = i, off
    if best is None:
        j = Judgement(None, "extra", 0.0, s.finger)
        return replace(st, extra=st.extra + 1, streak=0, log=st.log + ((None, "extra", 0.0, s.finger),)), j
    n = score.notes[best]
    if n.finger != s.finger:
        return replace(st, hit=st.hit | {best}, wrong=st.wrong + 1, streak=0,
                       log=st.log + ((best, "wrong_finger", best_off, s.finger),)), Judgement(best, "wrong_finger", best_off, s.finger)
    a = abs(best_off)
    if a <= PERFECT_MS:
        v, pts = "perfect", 100
    elif a <= GOOD_MS:
        v, pts = "good", 60
    else:
        v, pts = ("late" if best_off > 0 else "early"), 25
    mult = 1 + min(st.streak, 20) // 5 * 0.25
    return replace(st, hit=st.hit | {best}, streak=st.streak + 1, points=st.points + int(pts * mult),
                   perfect=st.perfect + (v == "perfect"), good=st.good + (v == "good"),
                   log=st.log + ((best, v, best_off, s.finger),)), Judgement(best, v, best_off, s.finger)


def sweep_misses(score: Score, st: PlayState, now_s: float) -> tuple[PlayState, list[int]]:
    """Notes whose window closed without a hit."""
    missed = [i for i in range(len(score.notes)) if i not in st.hit and (now_s - note_time_s(score, i, st.start_s)) * 1000 > MISS_MS]
    if not missed:
        return st, []
    return replace(st, hit=st.hit | set(missed), misses=st.misses + len(missed), streak=0,
                   log=st.log + tuple((i, "miss", 0.0, score.notes[i].finger) for i in missed)), missed


def upcoming(score: Score, st: PlayState, now_s: float, horizon_s: float) -> list[int]:
    return [i for i in range(len(score.notes)) if i not in st.hit and 0 <= note_time_s(score, i, st.start_s) - now_s <= horizon_s]


def summary(score: Score, st: PlayState) -> dict:
    total = len(score.notes) or 1
    acc = (st.perfect + st.good) / total
    return {"points": st.points, "accuracy": round(acc, 3), "perfect": st.perfect, "good": st.good,
            "misses": st.misses, "wrong_finger": st.wrong, "extra": st.extra, "notes": len(score.notes),
            "stars": 3 if acc > 0.9 else 2 if acc > 0.7 else 1 if acc > 0.4 else 0}
