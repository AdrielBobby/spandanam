"""Asan's voice and ears. TTS via espeak-ng (offline, has Malayalam) or macOS `say`; STT via Gemma 3n audio itself."""
from __future__ import annotations

import logging
import os
import shutil
import subprocess

log = logging.getLogger(__name__)
_ACTIVE: list = []          # running TTS processes, so stop() can kill them (tab closed, Stop pressed)


def _run(cmd: list[str]) -> None:
    try:
        p = subprocess.Popen(cmd); _ACTIVE.append(p); p.wait()
    except Exception as e:
        log.debug("tts failed: %s", e)
    finally:
        try: _ACTIVE.remove(p)
        except Exception: pass


def stop() -> None:
    """Kill any speaking/chanting process immediately."""
    for p in list(_ACTIVE):
        try: p.kill()
        except Exception: pass
    _ACTIVE.clear()
    for name in ("say", "espeak-ng"):
        subprocess.run(["pkill", "-x", name], check=False, capture_output=True)

# Vaaythari syllables in Devanagari so an Indic TTS voice pronounces them like a Malayali would, not like "ta" in English.
SYL_DEVA = {"tha": "ता", "ki": "कि", "ta": "ट", "ka": "क", "dhi": "धि", "mi": "मि", "dhim": "धिम्", "thom": "थोम्", "num": "नुम्", "ri": "रि",
            "dha": "धा", "na": "ना", "tin": "तिन्", "te": "टे", "ke": "के", "ge": "गे", "nam": "नम्", "dhin": "धिन्"}


def _mac_voices() -> set[str]:
    try:
        out = subprocess.run(["say", "-v", "?"], capture_output=True, text=True, timeout=5).stdout
        return {line.split()[0] for line in out.splitlines() if line.strip()}
    except Exception:
        return set()


def chant_voice() -> tuple[str | None, bool]:
    """(voice name, use_devanagari). THAALAM_VOICE overrides. Prefer Lekha (hi_IN, Indic phonology) > Rishi/Aman (en_IN) > default."""
    forced = os.environ.get("THAALAM_VOICE")
    voices = _mac_voices()
    if forced:
        return forced, forced.lower() in ("lekha",)
    for v, deva in (("Lekha", True), ("Rishi", False), ("Aman", False), ("Tara", False)):
        if v in voices:
            return v, deva
    return None, False


def _chant_text(syllables: tuple[str, ...], devanagari: bool) -> str:
    return " ".join(SYL_DEVA.get(x.lower(), x) if devanagari else x for x in syllables)


def speak(text: str, lang: str = "ml") -> None:
    if not text or os.environ.get("THAALAM_MUTE") == "1":
        return
    if shutil.which("espeak-ng"):
        _run(["espeak-ng", "-v", lang if lang != "en" else "en", "-s", "140", text])
    elif shutil.which("say"):
        _run(["say", text])
    else:
        log.info("ASAN: %s", text)


def chant(syllables: tuple[str, ...], bpm: float) -> None:
    """Chant the vaaythari at tempo (used together with the buzzer taps)."""
    if os.environ.get("THAALAM_MUTE") == "1":
        return
    beat = 60.0 / bpm
    if shutil.which("espeak-ng"):                                   # Pi/Linux: Hindi voice + Devanagari for Indic phonology
        _run(["espeak-ng", "-v", "hi", "-s", str(int(60 * 60 / beat / 10)), _chant_text(syllables, True)])
    elif shutil.which("say"):                                       # macOS: Lekha (hi_IN) if installed, else Indian English
        voice, deva = chant_voice()
        cmd = ["say", "-r", str(int(60 / beat * 1.2))] + (["-v", voice] if voice else []) + [_chant_text(syllables, deva)]
        _run(cmd)
    else:
        log.info("CHANT: %s", " ".join(syllables))
