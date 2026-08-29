"""Build an authentic kit from the learned recording itself: for each timbre cluster, cut the cleanest isolated strike
(strong onset, nothing else within a window) and save it as assets/kits/<name>/<finger>.wav. Listen/Practice then play
the real drum, not a synth. Kits derived from user uploads stay local (assets/kits is git-ignored)."""
from __future__ import annotations

import logging
from pathlib import Path

import numpy as np

from .transcribe import Transcription

log = logging.getLogger(__name__)
KITS_DIR = Path(__file__).resolve().parents[2] / "assets" / "kits"


def _isolation(times: np.ndarray, i: int) -> float:
    """Seconds to the nearest other onset (bigger = cleaner sample)."""
    others = np.delete(times, i)
    return float(np.min(np.abs(others - times[i]))) if others.size else 9.0


def pick_strikes(tr: Transcription, cluster_to_finger: dict[int, int], min_gap_s: float = 0.18) -> dict[int, float]:
    """finger -> onset time of the best sample: prefer isolated, then strong."""
    times = np.array([o.t_s for o in tr.onsets])
    best: dict[int, tuple[float, float]] = {}
    for i, o in enumerate(tr.onsets):
        f = cluster_to_finger.get(o.cluster, o.cluster % 5)
        iso = _isolation(times, i)
        key = (min(iso, 0.6), o.strength)              # isolation first (capped), then strength
        if f not in best or key > (best[f][0], best[f][1]):
            best[f] = (key[0], key[1], o.t_s)
    return {f: v[2] for f, v in best.items() if v[0] >= min_gap_s * 0.5}


def build_kit(path: Path, tr: Transcription, cluster_to_finger: dict[int, int], name: str,
              length_s: float = 0.45, sr: int = 22050) -> Path | None:
    import librosa, soundfile as sf
    y, _ = librosa.load(str(path), sr=sr, mono=True)
    picks = pick_strikes(tr, cluster_to_finger)
    if len(picks) < 3:
        log.info("kit not built for %s: only %d clean strikes", name, len(picks)); return None
    out = KITS_DIR / name; out.mkdir(parents=True, exist_ok=True)
    n = int(length_s * sr); fade = np.linspace(1, 0, int(0.08 * sr)) ** 2
    for f in range(5):
        t = picks.get(f)
        if t is None:                                   # missing finger: reuse the nearest available finger's sample
            t = picks[min(picks, key=lambda k: abs(k - f))]
        i0 = max(0, int((t - 0.005) * sr)); seg = y[i0:i0 + n].copy()
        if seg.size < n: seg = np.pad(seg, (0, n - seg.size))
        seg[-fade.size:] *= fade
        peak = float(np.abs(seg).max()) or 1.0
        sf.write(out / f"{f}.wav", (seg / peak * 0.9).astype(np.float32), sr)
    log.info("built kit %s from %s (%d fingers sampled)", name, path.name, len(picks))
    return out
