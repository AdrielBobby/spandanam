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
Compose ONE vaaythari phrase using only these syllables: {SYLS}. Syllable→finger: {json.dumps(SYLLABLE_FINGER)}.
You are given the TARGET for this level: exact number of syllables, bpm, and minimum number of distinct fingers. Meet it exactly.
The phrase must differ from every phrase in previous_rounds. Make it musical: a repeated motif with one twist.
Add one line of warm Maveli banter in English (<=12 words). You may use 'sheri' (okay), 'kollam' (meaning 'great!', not the town),
'mone'/'mole' (son/daughter). Return ONLY JSON: {{"phrase":["tha","ki","ta"],"bpm":72,"banter":"Sheri! Follow my fingers, mone."}}"""


def level_target(level: int) -> dict:
    n = min(8, 2 + level)                       # L1=3 … L6+=8 syllables
    return {"syllables": n, "bpm": min(160, 60 + 14 * (level - 1)), "min_distinct_fingers": min(5, 1 + (level + 1) // 2)}

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


def parse_round(content: str, level: int, previous: list[list[str]] | None = None) -> Round | None:
    d = normalize_keys(json.loads(content))
    phrase = tuple(s for s in d.get("phrase", []) if s in SYLLABLE_FINGER)
    tgt = level_target(level)
    if len(phrase) < 3 or abs(len(phrase) - tgt["syllables"]) > 1:
        return None
    if len({SYLLABLE_FINGER[s] for s in phrase}) < tgt["min_distinct_fingers"]:
        return None
    if previous and list(phrase) in previous:
        return None
    bpm = float(min(160, max(50, d.get("bpm", tgt["bpm"]))))
    return Round(level, phrase[:8], bpm, str(d.get("banter", ""))[:80], "gemma")


async def next_round(client: httpx.AsyncClient, url: str, model: str, level: int, history: list[dict]) -> Round:
    user = json.dumps({"level": level, "target": level_target(level), "previous_rounds": history[-4:]})
    c = await _chat(client, url, model, GAME_SYS, user, None, 160)
    try:
        r = parse_round(c, level, [h.get("phrase", []) for h in history]) if c else None
    except (json.JSONDecodeError, ValueError, TypeError):
        r = None
    return r or ladder_round(level)
