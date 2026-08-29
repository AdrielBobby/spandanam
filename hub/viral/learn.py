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
from .transcribe import quantize_onsets, refine_tempo, transcribe

log = logging.getLogger(__name__)


def build_score(events: list[tuple[float, int, float]], st: Structure, bpm: float) -> Score:
    notes = tuple(sorted((Note(b, st.cluster_to_finger.get(c, c % 5), s, st.syllables[st.cluster_to_finger.get(c, c % 5)])
                          for b, c, s in events), key=lambda n: n.beat))
    fmap = FingerMap(st.names, tuple(FINGER_COLORS), st.syllables)
    return Score(st.title, bpm, st.beats_per_cycle, notes, fmap, st.kit, st.thaalam, st.phrases)


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


def _cache_path(path: Path, model: str) -> Path:
    h = hashlib.sha1(path.read_bytes()).hexdigest()[:12]
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
    events = quantize_onsets(tr, bpm)
    n_beats = (events[-1][0] + 1) if events else 8.0
    fb = default_structure(bpm, n_beats)
    async with httpx.AsyncClient() as client:
        st = await structure(client, ollama_url, model, bpm, tr.cluster_profile, events, _clip_wav(str(path)) if use_audio else None, fb, scores)
    score = build_score(events, st, bpm)
    if score.title == "untitled":
        score = Score(path.stem, score.bpm, score.beats_per_cycle, score.notes, score.finger_map, score.kit, score.thaalam, score.phrases)
    if use_cache:
        from dataclasses import asdict
        try:
            cache.write_text(json.dumps({"score": json.loads(score.to_json()), "structure": asdict(st)}, ensure_ascii=False))
        except OSError as e:
            log.debug("cache write failed: %s", e)
    return score, st
