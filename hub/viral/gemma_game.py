"""Gemma 3n on-device: "Repeat after Maveli" — generates ever-harder one-cycle phrases with a little Onam banter.

Deterministic fallback ladder guarantees the game never stalls if Gemma is slow or returns junk.
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass

import httpx

from asan.config import SYLLABLE_FINGER
from .gemma_thaalam import _chat, normalize_keys

log = logging.getLogger(__name__)

SYLS = ", ".join(SYLLABLE_FINGER)

GAME_SYS = f"""You are Maveli, the beloved Onam king, playing "Repeat after Maveli" with a percussion glove player.
Compose ONE short vaaythari phrase for the given level using only these syllables: {SYLS}.
Level 1 = 3 syllables, slow, two fingers. Each level adds difficulty: more syllables (max 8), faster bpm (60→160),
more distinct fingers, off-beat feel (repeat a syllable) at level 5+. Keep it musical and repeatable.
Add one line of warm Maveli banter (English, <=12 words, may include one Malayalam word like 'kollam', 'sheri', 'mole/mone').
Return ONLY JSON: {{"phrase":["tha","ki","ta"],"bpm":72,"banter":"Sheri! Now follow my fingers, mone."}}"""

LADDER = [(["tha", "ki", "ta"], 66), (["dhim", "tha", "ka", "ta"], 76), (["tha", "ka", "dhi", "mi"], 88),
          (["dhim", "tha", "ka", "tha", "ki", "ta"], 96), (["thom", "ta", "ta", "ki", "ta", "ka"], 108),
          (["dhim", "tha", "ka", "dhi", "mi", "tha", "ki", "ta"], 120), (["thom", "ka", "ta", "ki", "ta", "ka", "dhi", "mi"], 136)]
BANTER = ["Sheri, let's begin!", "Kollam! A little faster now.", "Maveli is watching your ring finger…",
          "Now we're drumming, mone!", "Onam spirit! Keep it steady.", "Legend level. Don't blink.", "You might be the next asan."]


@dataclass(frozen=True)
class Round:
    level: int
    phrase: tuple[str, ...]
    bpm: float
    banter: str
    source: str  # "gemma" | "ladder"


def ladder_round(level: int) -> Round:
    i = min(max(level, 1), len(LADDER)) - 1
    p, b = LADDER[i]
    return Round(level, tuple(p), float(b), BANTER[i], "ladder")


def parse_round(content: str, level: int) -> Round | None:
    d = normalize_keys(json.loads(content))
    phrase = tuple(s for s in d.get("phrase", []) if s in SYLLABLE_FINGER)
    if len(phrase) < 3:
        return None
    bpm = float(min(160, max(50, d.get("bpm", 60 + 12 * level))))
    return Round(level, phrase[:8], bpm, str(d.get("banter", ""))[:80], "gemma")


async def next_round(client: httpx.AsyncClient, url: str, model: str, level: int, history: list[dict]) -> Round:
    user = json.dumps({"level": level, "previous_rounds": history[-3:]})
    c = await _chat(client, url, model, GAME_SYS, user, None, 160)
    try:
        r = parse_round(c, level) if c else None
    except (json.JSONDecodeError, ValueError, TypeError):
        r = None
    return r or ladder_round(level)
