"""Optional mic capture: 2 s WAV clips of the ensemble for Gemma 3n audio input."""
from __future__ import annotations

import io
import logging
import wave

log = logging.getLogger(__name__)


def record_clip(seconds: float = 2.0, rate: int = 16000) -> bytes | None:
    try:
        import numpy as np
        import sounddevice as sd
    except ImportError:
        return None
    try:
        data = sd.rec(int(seconds * rate), samplerate=rate, channels=1, dtype="int16")
        sd.wait()
    except Exception as e:  # device missing at venue is not fatal
        log.warning("mic capture failed: %s", e)
        return None
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(rate)
        w.writeframes(np.asarray(data).tobytes())
    return buf.getvalue()
