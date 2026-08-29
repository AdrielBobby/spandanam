"""Offline fallback composer: Gemma 3n writes a symbolic finger score when Gemini is unavailable (quota, no internet)."""
from __future__ import annotations

import json
import logging

import httpx

from asan.config import SYLLABLE_FINGER
from .config import KITS
from .gemma_thaalam import _chat, normalize_keys
from .score import Score, score_from_dict

log = logging.getLogger(__name__)

SYS = f"""You compose percussion for a 5-finger air-drum glove. Fingers 0..4 = thumb..pinky; thumb = bass, pinky = brightest.
Use vaaythari syllables from: {", ".join(SYLLABLE_FINGER)} (syllable→finger: {json.dumps(SYLLABLE_FINGER)}).
Write a learnable piece: a repeated motif, one variation, and a short kalasham (ending flourish) in the last cycle.
Notes are (beat, finger, label) with beat counted from 0 in quarter-beat steps. Return ONLY JSON:
{{"title":"","bpm":90,"beats_per_cycle":8,"kit":"chenda","thaalam":"chempada 8",
 "finger_map":{{"names":["","","","",""],"syllables":["","","","",""]}},
 "notes":[{{"beat":0.0,"finger":0,"velocity":1.0,"label":"thom"}}],"phrases":[[0,8]]}}"""

FINGER_IDX = {"thumb": 0, "index": 1, "middle": 2, "ring": 3, "pinky": 4}


async def compose_gemma(client: httpx.AsyncClient, url: str, model: str, brief: str, kit: str, thaalam: str,
                        cycles: int, bpm: float) -> Score:
    user = json.dumps({"brief": brief, "kit": kit if kit in KITS else "chenda", "thaalam": thaalam, "cycles": cycles, "bpm": bpm,
                       "kit_voices": KITS.get(kit, KITS["chenda"])["voices"]})
    c = await _chat(client, url, model, SYS, user, None, 1400)
    d = normalize_keys(json.loads(c)) if c else {}
    # coerce labels -> fingers when the model gave syllables but sloppy finger indices
    notes = []
    for n in d.get("notes", []):
        lab = str(n.get("label", "")).lower()
        f = FINGER_IDX.get(SYLLABLE_FINGER.get(lab, ""), n.get("finger", 0))
        notes.append({"beat": n.get("beat", 0), "finger": f, "velocity": n.get("velocity", 1.0), "label": lab})
    d["notes"] = notes
    d.setdefault("bpm", bpm); d.setdefault("kit", kit); d.setdefault("thaalam", thaalam)
    sc = score_from_dict(d)
    if len(sc.notes) < 4:
        raise ValueError("Gemma composition too short")
    return sc
