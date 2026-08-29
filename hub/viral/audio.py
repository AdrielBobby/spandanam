"""Mic capture -> 16 kHz mono WAV bytes."""
from __future__ import annotations

import io
import logging
import wave

log = logging.getLogger(__name__)


def record_clip(seconds: float, rate: int = 16000) -> bytes | None:
    try:
        import numpy as np
        import sounddevice as sd
        data = sd.rec(int(seconds * rate), samplerate=rate, channels=1, dtype="int16"); sd.wait()
    except Exception as e:
        log.warning("mic capture failed: %s", e); return None
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(rate); w.writeframes(np.asarray(data).tobytes())
    return buf.getvalue()
