"""Generate a synthetic 5-voice percussion track (WAV) for testing the learn pipeline without a real recording.
python -m viral.synth_track out.wav --bpm 96 --cycles 4
"""
from __future__ import annotations

import argparse

import numpy as np

from .sound import KIT_PARAMS, SR, _drum

# A chempada-ish 8-beat pattern over 5 voices (voice index = timbre low→high). Second half differs from the first
# (answer phrase + cymbal on 8) so the true period is 8, not 4.
PATTERN = [(0, 0), (0.5, 2), (1, 1), (1.5, 2), (2, 0), (2.5, 3), (3, 1), (3.5, 4),
           (4, 0), (4.5, 1), (5, 3), (5.5, 1), (6, 2), (6.5, 2), (7, 0), (7.5, 4), (7.75, 4)]


def render(bpm: float, cycles: int, kit: str = "chenda", seed: int = 0) -> np.ndarray:
    beat = 60.0 / bpm
    total = int(SR * (beat * 8 * cycles + 1.0))
    out = np.zeros(total, dtype=np.float32)
    voices = [_drum(*p).astype(np.float32) for p in KIT_PARAMS[kit]]
    rng = np.random.default_rng(seed)
    for c in range(cycles):
        for b, v in PATTERN:
            t = (c * 8 + b) * beat + rng.normal(0, 0.004)          # ±4 ms human jitter
            i = int(max(0, t) * SR); w = voices[v] * (0.7 + 0.3 * rng.random())
            out[i:i + len(w)] += w[: max(0, total - i)]
    return out / max(1e-6, np.abs(out).max()) * 0.9


def main() -> None:
    import soundfile as sf
    ap = argparse.ArgumentParser(); ap.add_argument("out"); ap.add_argument("--bpm", type=float, default=96); ap.add_argument("--cycles", type=int, default=4)
    ap.add_argument("--kit", default="chenda"); a = ap.parse_args()
    sf.write(a.out, render(a.bpm, a.cycles, a.kit), SR); print("wrote", a.out)


if __name__ == "__main__":
    main()
