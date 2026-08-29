"""Mic capture: 10 ms hops for DSP, rolling 2 s buffer for Gemma."""
from __future__ import annotations

import io
import wave
from collections import deque

import numpy as np


class MicBuffer:
    def __init__(self, sr: int, clip_s: float):
        self.sr = sr
        self.buf: deque = deque(maxlen=int(sr * clip_s))

    def push(self, frame: np.ndarray) -> None:
        self.buf.extend(frame.tolist())

    def wav(self) -> bytes:
        data = (np.clip(np.array(self.buf, dtype=np.float32), -1, 1) * 32767).astype(np.int16)
        b = io.BytesIO()
        with wave.open(b, "wb") as w:
            w.setnchannels(1); w.setsampwidth(2); w.setframerate(self.sr); w.writeframes(data.tobytes())
        return b.getvalue()


def open_stream(sr: int, hop: int, callback):
    import sounddevice as sd
    return sd.InputStream(samplerate=sr, channels=1, blocksize=hop, dtype="float32", callback=callback)
