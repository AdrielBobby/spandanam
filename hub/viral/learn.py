"""Learn pipeline: audio file -> transcription (deterministic) -> Gemma structure -> finger Score."""
from __future__ import annotations

import hashlib
import json
import logging
from pathlib import Path

import httpx

from .config import FINGER_COLORS
from .gemma_thaalam import Structure, default_structure, structure
from .score import FingerMap, Note, Score
from .transcribe import normalize_octave, quantize_onsets, refine_tempo, transcribe

log = logging.getLogger(__name__)


def thin_events(events: list[tuple[float, int, float]], cluster_to_finger: dict[int, int],
                min_gap_beats: float = 0.5, max_per_beat: int = 2) -> list[tuple[float, int, float]]:
    """Make a playable score out of raw onsets: per finger, merge hits closer than min_gap_beats (keep the strongest);
    then cap notes per beat slot (keep the strongest). Learned melam is dense; a rhythm game is not."""
    by_finger: dict[int, list[tuple[float, int, float]]] = {}
    for b, c, s in sorted(events):
        f = cluster_to_finger.get(c, c % 5)
        lst = by_finger.setdefault(f, [])
        if lst and b - lst[-1][0] < min_gap_beats:
            if s > lst[-1][2]: lst[-1] = (b, c, s)
        else:
            lst.append((b, c, s))
    merged = sorted(x for lst in by_finger.values() for x in lst)
    out: list = []; slot: dict = {}
    for b, c, s in merged:
        slot.setdefault(int(b), []).append((s, b, c))
    for k in sorted(slot):
        keep = sorted(slot[k], reverse=True)[:max_per_beat]
        out += [(b, c, s) for s, b, c in sorted(keep, key=lambda x: x[1])]
    return out


def build_score(events: list[tuple[float, int, float]], st: Structure, bpm: float, thin: bool = True) -> Score:
    if thin:
        events = thin_events(events, st.cluster_to_finger)
    notes = tuple(sorted((Note(b, st.cluster_to_finger.get(c, c % 5), s, st.syllables[st.cluster_to_finger.get(c, c % 5)])
                          for b, c, s in events), key=lambda n: n.beat))
    fmap = FingerMap(st.names, tuple(FINGER_COLORS), st.syllables)
    return Score(st.title, bpm, st.beats_per_cycle, notes, fmap, st.kit, st.thaalam, st.phrases)


def reconcile_cycle(st: Structure, scores: dict[int, float], bpm: float) -> Structure:
    """Math decides when the evidence is strong; Gemma may only pick a related length (x2 / x0.5)."""
    from dataclasses import replace
    from .transcribe import pick_cycle
    guess = pick_cycle(scores); mx = max(scores.values()) if scores else 0.0
    # confidence is clamped by the evidence, never by Gemma's enthusiasm
    cap = 0.9 if mx > 0.35 else 0.5 if mx > 0.12 else 0.35
    if st.confidence > cap:
        st = replace(st, confidence=cap)
    if mx <= 0.12 and "uncertain" not in st.thaalam:
        st = replace(st, thaalam=f"{st.thaalam} — uncertain", evidence=(st.evidence + f" [periodicity only {mx:.2f}: treat the cycle as a guess]").strip())
    related = {guess, guess * 2, guess // 2 if guess % 2 == 0 else guess}
    if mx > 0.35 and st.beats_per_cycle not in related:
        log.info("cycle override: gemma %s -> evidence %s (score %.2f)", st.beats_per_cycle, guess, mx)
        names = {3: "thakita/roopakam (3)", 4: "ekam (4)", 5: "khanda (5)", 6: "panchari (6)", 7: "thriputa/pandi (7)", 8: "chempada/adi (8)", 12: "panchari (12)", 14: "pandi (14)", 16: "chempada (16)"}
        n = guess
        return replace(st, beats_per_cycle=n, thaalam=names.get(n, f"{n}-beat cycle"),
                       phrases=tuple((0.0, float(n * k)) for k in (1, 2, 4) if n * k <= max(p[1] for p in st.phrases) or k == 1),
                       evidence=(st.evidence + f" [cycle set to {n} by periodicity {mx:.2f}]").strip())
    return st


def _clip_wav(path: str, seconds: float = 6.0) -> bytes | None:
    try:
        import io, wave
        import librosa, numpy as np
        y, sr = librosa.load(path, sr=16000, mono=True, duration=seconds)
        b = io.BytesIO()
        with wave.open(b, "wb") as w:
            w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes((np.clip(y, -1, 1) * 32767).astype("int16").tobytes())
        return b.getvalue()
    except Exception as e:
        log.debug("clip failed: %s", e); return None


ALGO_VERSION = "v8-synth-default"     # bump when transcription/digest logic changes so stale caches are ignored


def _cache_path(path: Path, model: str) -> Path:
    h = hashlib.sha1(path.read_bytes() + ALGO_VERSION.encode()).hexdigest()[:12]
    return path.with_name(f".{path.stem}.{h}.{model.replace(':', '_')}.score.json")


async def learn_from_file(path: Path, ollama_url: str, model: str, use_audio: bool = True, use_cache: bool = True) -> tuple[Score, Structure]:
    """Audio -> Score. Cached per (file content, model) so re-learning a demo track is instant."""
    cache = _cache_path(path, model)
    if use_cache and cache.exists():
        try:
            d = json.loads(cache.read_text())
            from .score import score_from_dict
            st = Structure(**{k: (tuple(v) if isinstance(v, list) and k in ("names", "syllables") else
                                  tuple(tuple(x) for x in v) if k == "phrases" else
                                  {int(a): int(b) for a, b in v.items()} if k == "cluster_to_finger" else v)
                              for k, v in d["structure"].items()})
            log.info("learn cache hit %s", cache.name)
            return score_from_dict(d["score"]), st
        except Exception as e:  # corrupt cache -> recompute
            log.warning("cache unreadable (%s), recomputing", e)
    tr = transcribe(str(path))
    bpm, scores = refine_tempo(tr)                      # octave + drift corrected
    bpm, scores = normalize_octave(tr, bpm, scores)     # count at a moderate pulse (176×16 -> 88×8)
    events = quantize_onsets(tr, bpm)
    n_beats = (events[-1][0] + 1) if events else 8.0
    fb = default_structure(bpm, n_beats)
    async with httpx.AsyncClient() as client:
        st = await structure(client, ollama_url, model, bpm, tr.cluster_profile, events, _clip_wav(str(path)) if use_audio else None, fb, scores)
    st = reconcile_cycle(st, scores, bpm)
    score = build_score(events, st, bpm)
    import os
    if os.environ.get("REAL_KITS") == "1":              # opt-in: sample real strikes from this recording (off by default — synth kits sound better)
        try:
            from .sample_kit import build_kit
            kit_dir = build_kit(path, tr, st.cluster_to_finger, f"track_{path.stem}")
        except Exception as e:
            kit_dir = None; log.warning("real kit not built: %s", e)
        if kit_dir:
            score = Score(score.title, score.bpm, score.beats_per_cycle, score.notes, score.finger_map, kit_dir.name, score.thaalam, score.phrases)
    if score.title == "untitled":
        score = Score(path.stem, score.bpm, score.beats_per_cycle, score.notes, score.finger_map, score.kit, score.thaalam, score.phrases)
    if use_cache:
        from dataclasses import asdict
        try:
            cache.write_text(json.dumps({"score": json.loads(score.to_json()), "structure": asdict(st)}, ensure_ascii=False))
        except OSError as e:
            log.debug("cache write failed: %s", e)
    return score, st
