"""Learn pipeline: audio file -> transcription (deterministic) -> Gemma structure -> finger Score."""
from __future__ import annotations

import logging
from pathlib import Path

import httpx

from .config import FINGER_COLORS
from .gemma_thaalam import Structure, default_structure, structure
from .score import FingerMap, Note, Score
from .transcribe import onsets_to_beats, transcribe

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


async def learn_from_file(path: Path, ollama_url: str, model: str, use_audio: bool = True) -> tuple[Score, Structure]:
    tr = transcribe(str(path))
    events = onsets_to_beats(tr, tr.bpm)
    n_beats = (events[-1][0] + 1) if events else 8.0
    fb = default_structure(tr.bpm, n_beats)
    async with httpx.AsyncClient() as client:
        st = await structure(client, ollama_url, model, tr.bpm, tr.cluster_profile, events, _clip_wav(str(path)) if use_audio else None, fb)
    score = build_score(events, st, tr.bpm)
    if score.title == "untitled":
        score = Score(path.stem, score.bpm, score.beats_per_cycle, score.notes, score.finger_map, score.kit, score.thaalam, score.phrases)
    return score, st
