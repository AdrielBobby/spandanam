"""Gemma 3n on-device: the musical understanding that DSP cannot provide.

Every 2 s it hears the ensemble clip and returns:
 - which instruments are actually playing (not just which bands have energy)
 - the kaalam (tempo stage) and imminent events (kaalam change, kombu solo, kalasham/climax)
 - a body map + per-band gains: HOW the melam should be felt right now
 - a caption for the wearer's screen
 - a short haptic motif for events (a distinct pattern the wearer learns to recognise)
"""
from __future__ import annotations

import base64
import json
import logging
from dataclasses import dataclass

import httpx

from .config import DEFAULT_MAP, MOTORS

log = logging.getLogger(__name__)

SYSTEM = f"""You are the ears of a deaf listener at a Kerala chenda melam (Panchari/Pandi). You hear a 2-second clip
plus per-band energy stats. Decide how the music should be FELT on an 8-motor wearable: motors {list(MOTORS)}.
Instruments: valanthala (bass chenda), idanthala (treble chenda), elathalam (cymbals), kombu (horn), kuzhal (pipe).
Return ONLY JSON:
{{"instruments": ["..."], "kaalam": 1-5, "event": "none|kaalam_change|kombu_solo|kalasham|silence",
 "body_map": {{"bass": [motors], "treble": [motors], "horn": [motors], "cymbal": [motors]}},
 "gains": {{"bass": 0-1.5, "treble": 0-1.5, "horn": 0-1.5, "cymbal": 0-1.5}},
 "motif": {{"<motor>": 0-255}} or {{}},
 "caption_en": "<=12 words", "caption_ml": "<=12 words in Malayalam"}}
Principles: bass on torso, fast treble on wrists, sustained horns as steady shoulder hum, cymbals on fingertips.
In kalasham raise all gains and add a back motif. On kaalam_change give a 3-pulse wrist motif. Keep silence quiet.
Respect the listener's preferences given in the prompt."""


@dataclass(frozen=True)
class Hearing:
    instruments: tuple[str, ...]
    kaalam: int
    event: str
    body_map: dict[str, tuple[str, ...]]
    gains: dict[str, float]
    motif: dict[str, int]
    caption_en: str
    caption_ml: str
    raw: str


DEFAULT_HEARING = Hearing((), 1, "none", DEFAULT_MAP, {b: 1.0 for b in DEFAULT_MAP}, {}, "listening…", "കേൾക്കുന്നു…", "{}")


def parse_hearing(content: str) -> Hearing:
    d = json.loads(content)
    bm = {b: tuple(m for m in v if m in MOTORS) for b, v in d.get("body_map", {}).items()} or DEFAULT_MAP
    gains = {b: float(min(1.5, max(0.0, g))) for b, g in d.get("gains", {}).items()} or {b: 1.0 for b in DEFAULT_MAP}
    motif = {m: int(min(255, max(0, v))) for m, v in d.get("motif", {}).items() if m in MOTORS}
    return Hearing(tuple(d.get("instruments", [])), int(d.get("kaalam", 1)), str(d.get("event", "none")),
                   bm, gains, motif, str(d.get("caption_en", "")), str(d.get("caption_ml", "")), content)


async def hear(client: httpx.AsyncClient, url: str, model: str, wav: bytes, stats: dict,
               preferences: str) -> Hearing | None:
    prompt = json.dumps({"band_levels": stats, "listener_preferences": preferences})
    body = {"model": model, "stream": False, "format": "json",
            "messages": [{"role": "system", "content": SYSTEM},
                         {"role": "user", "content": prompt, "audio": [base64.b64encode(wav).decode()]}],
            "options": {"temperature": 0.2, "num_predict": 400}}
    try:
        r = await client.post(f"{url}/api/chat", json=body, timeout=10.0)
        r.raise_for_status()
        return parse_hearing(r.json()["message"]["content"])
    except (httpx.HTTPError, json.JSONDecodeError, KeyError, ValueError) as e:
        log.warning("gemma hear failed: %s", e)
        return None
