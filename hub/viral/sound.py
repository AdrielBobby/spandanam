"""Speaker output. Synth percussion kits (no sample files needed); drops in WAV samples if assets/kits/<kit>/<i>.wav exist."""
from __future__ import annotations

import logging
from pathlib import Path

import numpy as np

log = logging.getLogger(__name__)
SR = 22050


def _env(n: int, decay: float) -> np.ndarray:
    return np.exp(-np.linspace(0, decay, n))


def _drum(freq: float, dur: float, decay: float, noise: float, pitch_drop: float = 0.0) -> np.ndarray:
    n = int(SR * dur); t = np.arange(n) / SR
    f = freq * (1 - pitch_drop * t / dur)
    tone = np.sin(2 * np.pi * np.cumsum(f) / SR)
    nz = np.random.default_rng(0).standard_normal(n)
    return ((1 - noise) * tone + noise * nz) * _env(n, decay)


# per kit: 5 voices -> (freq, dur, decay, noise, pitch_drop)
KIT_PARAMS = {
    "chenda":    [(110, .5, 8, .15, .3), (420, .25, 14, .35, .2), (700, .12, 30, .5, .1), (1400, .1, 40, .7, 0), (300, .3, 10, .6, 0)],
    "mridangam": [(90, .6, 6, .05, .4), (260, .3, 12, .1, .1), (520, .25, 14, .15, .1), (900, .12, 35, .5, 0), (180, .2, 20, .3, .2)],
    "tabla":     [(80, .5, 6, .05, .5), (330, .3, 10, .1, 0), (600, .35, 8, .05, 0), (1100, .1, 40, .6, 0), (450, .1, 40, .7, 0)],
    "kit":       [(60, .4, 10, .1, .6), (200, .25, 16, .8, .2), (3000, .08, 60, 1.0, 0), (150, .35, 10, .2, .3), (2500, .6, 5, .9, 0)],
}


class Sampler:
    def __init__(self, kit: str, assets: Path | None = None):
        self.kit = kit
        self.buf = self._load(kit, assets)
        try:
            import sounddevice as sd
            self.sd = sd
        except Exception as e:  # headless dev
            log.warning("no audio device: %s", e); self.sd = None

    def _load(self, kit: str, assets: Path | None) -> list[np.ndarray]:
        out = []
        for i, p in enumerate(KIT_PARAMS.get(kit, KIT_PARAMS["kit"])):
            wav = assets / kit / f"{i}.wav" if assets else None
            if wav and wav.exists():
                import soundfile as sf
                d, _ = sf.read(wav, dtype="float32"); out.append(d.mean(axis=1) if d.ndim > 1 else d)
            else:
                out.append(_drum(*p).astype(np.float32))
        return out

    def set_kit(self, kit: str, assets: Path | None = None) -> None:
        self.kit, self.buf = kit, self._load(kit, assets)

    def play(self, finger: int, velocity: float = 1.0) -> None:
        if self.sd is None:
            return
        try:
            self.sd.play(self.buf[finger % 5] * float(min(1.0, velocity)), SR, blocking=False)
        except Exception as e:
            log.debug("play failed: %s", e)
