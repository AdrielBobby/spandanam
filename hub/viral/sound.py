"""Speaker output. Synth percussion kits (no sample files needed); drops in WAV samples if assets/kits/<kit>/<i>.wav exist."""
from __future__ import annotations

import logging
from pathlib import Path

import numpy as np

log = logging.getLogger(__name__)
SR = 22050


def _modal_drum(f0: float, dur: float, modes: tuple[tuple[float, float, float], ...], noise: float = 0.2,
                noise_dur: float = 0.01, pitch_drop: float = 0.0, click: float = 0.3, seed: int = 0) -> np.ndarray:
    """Physically-flavoured membrane: sum of overtone modes (ratio, amplitude, decay_s), a downward pitch glide on impact,
    a short filtered noise burst for the stick/skin contact, and a tiny click. Far closer to a drum than sine + noise."""
    n = int(SR * dur); t = np.arange(n) / SR
    glide = 1.0 + pitch_drop * np.exp(-t / 0.03)                      # quick pitch drop after the hit
    out = np.zeros(n)
    for ratio, amp, decay in modes:
        phase = 2 * np.pi * np.cumsum(f0 * ratio * glide) / SR
        out += amp * np.sin(phase) * np.exp(-t / decay)
    rng = np.random.default_rng(seed)
    nz = rng.standard_normal(n) * np.exp(-t / noise_dur)
    nz = np.convolve(nz, np.ones(3) / 3, mode="same")                  # soften the burst
    out += noise * nz
    out[: int(0.0008 * SR)] += click * np.linspace(1, 0, int(0.0008 * SR))
    out *= np.minimum(1.0, t / 0.0015)                                  # 1.5 ms attack, no click at t=0
    out /= max(1e-6, np.abs(out).max())
    return out.astype(np.float32)


# Circular-membrane mode ratios (1, 1.59, 2.14, 2.30, 2.65, 2.92) with per-instrument tuning.
CHENDA_VALANTHALA = (( 1.0, 1.0, 0.45), (1.59, 0.55, 0.22), (2.14, 0.35, 0.14), (2.65, 0.2, 0.09))
CHENDA_IDANTHALA  = (( 1.0, 1.0, 0.16), (1.59, 0.7, 0.10), (2.14, 0.5, 0.07), (2.92, 0.3, 0.05), (3.6, 0.2, 0.03))
MRIDANGAM_THOM    = (( 1.0, 1.0, 0.9),  (2.0, 0.25, 0.4),  (3.0, 0.1, 0.2))                       # harmonic (loaded head)
MRIDANGAM_NAM     = (( 1.0, 1.0, 0.5),  (2.0, 0.6, 0.35),  (3.0, 0.35, 0.2), (4.0, 0.2, 0.12))
TABLA_BAYAN       = (( 1.0, 1.0, 0.6),  (2.0, 0.15, 0.3))
TABLA_NA          = (( 1.0, 1.0, 0.45), (2.0, 0.7, 0.35),  (3.0, 0.4, 0.22), (4.0, 0.25, 0.15), (5.0, 0.1, 0.1))
KICK              = (( 1.0, 1.0, 0.35), (1.5, 0.2, 0.08))
SNARE             = (( 1.0, 0.8, 0.12), (1.6, 0.6, 0.08), (2.3, 0.4, 0.05))

# per kit: 5 voices low→high. (f0, dur, modes, noise, noise_dur, pitch_drop, click)
KIT_PARAMS = {
    "chenda": [
        (95,  1.2, CHENDA_VALANTHALA, 0.25, 0.012, 0.35, 0.4),    # valanthala – deep bass head
        (330, 0.5, CHENDA_IDANTHALA,  0.30, 0.008, 0.25, 0.6),    # idanthala open – bright, ringing
        (520, 0.22, CHENDA_IDANTHALA, 0.45, 0.006, 0.15, 0.8),    # idanthala closed – damped, crack
        (600, 0.11, ((1.0, 1.0, 0.05), (2.3, 0.45, 0.025)), 0.5, 0.005, 0.05, 0.55),  # rim / stick on edge — wood, not a beep
        (200, 0.15, CHENDA_VALANTHALA, 0.22, 0.006, 0.18, 0.35, 6),  # roll – 6 rapid low strokes on the head
    ],
    "mridangam": [
        (78,  1.4, MRIDANGAM_THOM, 0.08, 0.010, 0.6, 0.2),        # thom – gliding bass
        (245, 0.8, MRIDANGAM_NAM,  0.10, 0.006, 0.05, 0.4),       # nam – harmonic ring
        (490, 0.45, MRIDANGAM_NAM, 0.15, 0.005, 0.03, 0.5),       # dhin
        (700, 0.10, ((1.0, 1.0, 0.03), (2.0, 0.5, 0.02)), 0.7, 0.004, 0.0, 1.0),   # chapu – slap
        (180, 0.18, ((1.0, 1.0, 0.06), (1.6, 0.5, 0.04)), 0.4, 0.006, 0.2, 0.6),   # arai – muted
    ],
    "tabla": [
        (70,  1.1, TABLA_BAYAN, 0.06, 0.010, 0.8, 0.2),           # ge – bayan with glide
        (300, 0.7, TABLA_NA,    0.12, 0.005, 0.0, 0.5),           # na
        (600, 0.9, TABLA_NA,    0.08, 0.004, 0.0, 0.4),           # tin – high ringing
        (1000, 0.08, ((1.0, 1.0, 0.03),), 0.8, 0.004, 0.0, 1.0),  # te – closed slap
        (450, 0.10, ((1.0, 1.0, 0.04), (2.1, 0.5, 0.03)), 0.7, 0.004, 0.0, 0.9),   # ke
    ],
    "kit": [
        (55,  0.6, KICK,  0.10, 0.008, 0.9, 0.5),                 # kick
        (190, 0.35, SNARE, 0.9, 0.09, 0.15, 0.7),                 # snare – long noise body
        (3200, 0.10, ((1.0, 1.0, 0.03), (1.8, 0.6, 0.02)), 1.0, 0.03, 0.0, 0.6),   # hi-hat closed
        (140, 0.5, ((1.0, 1.0, 0.3), (1.5, 0.4, 0.15)), 0.2, 0.008, 0.35, 0.5),    # tom
        (2600, 1.6, ((1.0, 1.0, 1.2), (2.6, 0.6, 0.9), (4.2, 0.3, 0.6)), 0.5, 0.02, 0.0, 0.4),  # ride
    ],
}


def _roll(f0: float, dur: float, modes, noise: float, noise_dur: float, pitch_drop: float,
          click: float, strokes: int) -> np.ndarray:
    """A chenda roll is many rapid strokes on the head, not one long ring-out. Layer short
    damped strokes ~28 ms apart with slight timing/level unevenness so it reads as a hand
    roll rather than a machine tremolo."""
    stroke = _modal_drum(f0, dur, modes, noise, noise_dur, pitch_drop, click)
    gap = int(SR * 0.028)
    n = gap * (strokes - 1) + len(stroke)
    out = np.zeros(n, dtype=np.float32)
    rng = np.random.default_rng(7)
    for k in range(strokes):
        i = max(0, k * gap + int(rng.integers(-90, 90)))          # human unevenness
        amp = 0.55 + 0.45 * (1 - k / max(1, strokes - 1))          # slight decrescendo
        seg = stroke[: n - i]
        out[i : i + len(seg)] += seg * amp
    out /= max(1e-6, np.abs(out).max())
    return out.astype(np.float32)


def _drum(f0, dur, modes, noise=0.2, noise_dur=0.01, pitch_drop=0.0, click=0.3, strokes=0) -> np.ndarray:
    """strokes > 0 renders a roll of that many strokes; 0 (the default) a single hit."""
    if strokes:
        return _roll(f0, dur, modes, noise, noise_dur, pitch_drop, click, strokes)
    return _modal_drum(f0, dur, modes, noise, noise_dur, pitch_drop, click)


def render_kit_preview(kit: str, path: str, bpm: float = 100) -> None:
    """Write a short audition file: each voice twice, then a little pattern."""
    import soundfile as sf
    voices = [_drum(*p) for p in KIT_PARAMS[kit]]
    beat = 60 / bpm; seq = [(i * beat * 0.75, v) for i, v in enumerate([0, 0, 1, 1, 2, 2, 3, 3, 4, 4])]
    pat = [0, 2, 1, 2, 0, 3, 1, 4, 0, 2, 1, 2, 0, 3, 4, 4]
    seq += [(8 * beat + i * beat / 2, v) for i, v in enumerate(pat)]
    total = int(SR * (8 * beat + len(pat) * beat / 2 + 2)); out = np.zeros(total, dtype=np.float32)
    for t, v in seq:
        i = int(t * SR); w = voices[v]; out[i:i + len(w)] += w[: max(0, total - i)] * 0.8
    sf.write(path, out / max(1e-6, np.abs(out).max()) * 0.9, SR)


KITS_DIR = Path(__file__).resolve().parents[2] / "assets" / "kits"


class Mixer:
    """Persistent output stream that sums overlapping voices, so a new hit never cuts the previous one off."""

    def __init__(self, sr: int = SR, max_voices: int = 24):
        import sounddevice as sd
        import threading, time
        self.sd, self.sr, self.max_voices = sd, sr, max_voices
        self._voices: list[tuple[np.ndarray, int]] = []          # (buffer, position)
        self._lock = threading.Lock()
        self._time = time
        self._last_check = 0.0
        self.device_name = ""
        self.stream = None
        self._open()

    def _open(self) -> None:
        """(Re)open the output stream on the CURRENT system default device (headphones plugged in later, stage speaker...)."""
        if self.stream is not None:
            try: self.stream.stop(); self.stream.close()
            except Exception: pass
        self.sd.default.device = None                              # re-resolve the default
        info = self.sd.query_devices(kind="output")
        self.device_name = str(info["name"])
        self.stream = self.sd.OutputStream(samplerate=self.sr, channels=1, dtype="float32", blocksize=256, callback=self._cb)
        self.stream.start()
        log.info("audio output -> %s", self.device_name)

    def ensure_device(self) -> None:
        """Cheap poll (max every 2 s): if the OS default output changed, follow it."""
        now = self._time.monotonic()
        if now - self._last_check < 2.0:
            return
        self._last_check = now
        try:
            name = str(self.sd.query_devices(kind="output")["name"])   # NOTE: never re-init PortAudio here — it kills the live stream
        except Exception:
            return
        if name != self.device_name or not self.stream.active:
            log.info("output changed or stream dead: %s -> %s", self.device_name, name)
            self.reopen()

    def reopen(self) -> None:
        """Rebind to the current default output (call after plugging in headphones/speaker)."""
        with self._lock: self._voices = []
        try:
            self.sd._terminate(); self.sd._initialize()             # safe here: we are about to open a fresh stream
        except Exception: pass
        self._open()

    def _cb(self, out, frames, _time, _status):
        mix = np.zeros(frames, dtype=np.float32)
        with self._lock:
            alive = []
            for buf, pos in self._voices:
                chunk = buf[pos:pos + frames]
                mix[:chunk.size] += chunk
                if pos + frames < buf.size:
                    alive.append((buf, pos + frames))
            self._voices = alive
        np.clip(mix, -1.0, 1.0, out=mix)                       # soft ceiling
        out[:, 0] = mix

    def trigger(self, buf: np.ndarray) -> None:
        self.ensure_device()
        with self._lock:
            if len(self._voices) >= self.max_voices:
                self._voices.pop(0)
            self._voices.append((buf, 0))

    def stop(self) -> None:
        with self._lock:
            self._voices = []


class Sampler:
    def __init__(self, kit: str, assets: Path | None = None):
        self.kit = kit
        self.buf = self._load(kit, assets or KITS_DIR)
        self.mixer = None
        try:
            self.mixer = Mixer(SR)
            self.sd = self.mixer.sd
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
        self.kit, self.buf = kit, self._load(kit, assets or KITS_DIR)

    def play(self, finger: int, velocity: float = 1.0) -> None:
        if self.mixer is None:
            return
        try:
            self.mixer.trigger(self.buf[finger % 5] * float(min(1.0, max(0.15, velocity))))
        except Exception as e:
            log.debug("play failed: %s", e)

    def stop(self) -> None:
        if self.mixer: self.mixer.stop()
