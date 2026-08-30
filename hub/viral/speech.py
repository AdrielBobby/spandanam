"""Asan's voice and ears. TTS via espeak-ng (offline, has Malayalam) or macOS `say`; STT via Gemma 3n audio itself."""
from __future__ import annotations

import logging
import os
import shutil
import subprocess

log = logging.getLogger(__name__)


def speak(text: str, lang: str = "ml") -> None:
    if not text or os.environ.get("THAALAM_MUTE") == "1":
        return
    if shutil.which("espeak-ng"):
        subprocess.run(["espeak-ng", "-v", lang if lang != "en" else "en", "-s", "140", text], check=False)
    elif shutil.which("say"):
        subprocess.run(["say", text], check=False)
    else:
        log.info("ASAN: %s", text)


def chant(syllables: tuple[str, ...], bpm: float) -> None:
    """Chant the vaaythari at tempo (used together with the buzzer taps)."""
    if os.environ.get("THAALAM_MUTE") == "1":
        return
    beat = 60.0 / bpm
    if shutil.which("espeak-ng"):
        subprocess.run(["espeak-ng", "-s", str(int(60 * 60 / beat / 10)), " ".join(syllables)], check=False)
    elif shutil.which("say"):
        subprocess.run(["say", "-r", str(int(60 / beat * 1.2)), " ".join(syllables)], check=False)
    else:
        log.info("CHANT: %s", " ".join(syllables))
