"""Gemma 3n on-device — the musical brain.

structure(): transcription stats + quantised events (+ optional audio clip) -> thaalam name, cycle length,
             finger assignment (cluster->finger with voice names, syllables, colours), practice phrases, kaalam.
coach():     a play-through's judgement summary + weak spots -> specific, short coaching (EN + ML) and what to drill next.
"""
from __future__ import annotations

import base64
import json
import logging
from dataclasses import dataclass

import httpx

from .config import FINGERS, KITS

log = logging.getLogger(__name__)

STRUCT_SYS = """You are a Kerala percussion asan and music analyst. You receive: estimated bpm, timbre clusters 0-4 (0=lowest/bassiest,
4=brightest) with counts, and quantised events (beat, cluster, strength). Optionally a short audio clip. Decide:
- thaalam: name (e.g. chempada/adi 8, panchari 6, thriputa 7/14, ekam 4, roopakam 6/3, or 'free') and beats_per_cycle
- finger_map: which cluster plays on which finger (thumb..pinky). Bass to thumb, brightest to pinky unless the music says otherwise.
  Give each finger a voice name from the chosen kit and a vaaythari syllable (tha ki ta ka dhi mi dhim thom num ri).
- phrases: 3-6 practice segments as [start_beat, end_beat] of increasing difficulty, aligned to cycles.
- kit: chenda|mridangam|tabla|kit ; title: short; kaalam: 1-3 (tempo stage)
Return ONLY JSON: {"title":"","thaalam":"","beats_per_cycle":8,"kit":"chenda","kaalam":1,
 "finger_map":{"cluster_to_finger":{"0":0,"1":1,"2":2,"3":3,"4":4},"names":["","","","",""],"syllables":["","","","",""]},
 "phrases":[[0,8]], "notes_en":"<=25 words on the rhythm's character"}"""

COACH_SYS = """You are a warm, precise percussion teacher. Given a rhythm-game summary of one attempt (accuracy, per-finger
misses, early/late bias in ms, streaks, wrong fingers) and the finger names/syllables, give feedback like a real asan:
one specific observation, one fix, one drill (which phrase, what bpm). Return ONLY JSON:
{"say_en":"<=30 words","say_ml":"<=30 words in Malayalam","drill_phrase":index,"drill_bpm":number,"focus":"timing|finger|dynamics|reward"}"""


@dataclass(frozen=True)
class Structure:
    title: str
    thaalam: str
    beats_per_cycle: int
    kit: str
    kaalam: int
    cluster_to_finger: dict[int, int]
    names: tuple[str, ...]
    syllables: tuple[str, ...]
    phrases: tuple[tuple[float, float], ...]
    notes_en: str
    raw: str = "{}"


def default_structure(bpm_hint: float, n_beats: float) -> Structure:
    return Structure("untitled", "chempada (8)", 8, "chenda", 1, {i: i for i in range(5)},
                     tuple(KITS["chenda"]["voices"]), ("thom", "tha", "ki", "ta", "ri"),
                     tuple((float(s), float(min(s + 8, n_beats))) for s in range(0, int(n_beats), 8))[:6] or ((0.0, 8.0),),
                     "default mapping", "{}")


def parse_structure(content: str, fallback: Structure) -> Structure:
    d = json.loads(content)
    fm = d.get("finger_map", {})
    c2f = {int(k): int(v) % 5 for k, v in fm.get("cluster_to_finger", {}).items()} or fallback.cluster_to_finger
    kit = d.get("kit") if d.get("kit") in KITS else fallback.kit
    names = tuple((fm.get("names") or KITS[kit]["voices"])[:5]); names = names if len(names) == 5 else tuple(KITS[kit]["voices"])
    syl = tuple((fm.get("syllables") or fallback.syllables)[:5]); syl = syl if len(syl) == 5 else fallback.syllables
    phrases = tuple((float(a), float(b)) for a, b in d.get("phrases", []) if b > a) or fallback.phrases
    return Structure(str(d.get("title", fallback.title)), str(d.get("thaalam", fallback.thaalam)),
                     int(d.get("beats_per_cycle", fallback.beats_per_cycle)) or 8, kit, int(d.get("kaalam", 1)),
                     c2f, names, syl, phrases, str(d.get("notes_en", "")), content)


async def _chat(client: httpx.AsyncClient, url: str, model: str, system: str, user: str, wav: bytes | None, n: int) -> str | None:
    msg: dict = {"role": "user", "content": user}
    if wav:
        msg["audio"] = [base64.b64encode(wav).decode()]
    body = {"model": model, "stream": False, "format": "json", "options": {"temperature": 0.2, "num_predict": n},
            "messages": [{"role": "system", "content": system}, msg]}
    try:
        r = await client.post(f"{url}/api/chat", json=body, timeout=60.0); r.raise_for_status()
        return r.json()["message"]["content"]
    except (httpx.HTTPError, KeyError) as e:
        log.warning("gemma failed: %s", e); return None


async def structure(client, url, model, bpm: float, profile: dict, events: list[tuple[float, int, float]],
                    wav: bytes | None, fallback: Structure) -> Structure:
    user = json.dumps({"bpm": round(bpm, 1), "clusters": profile, "events": events[:240], "fingers": FINGERS})
    c = await _chat(client, url, model, STRUCT_SYS, user, wav, 500)
    try:
        return parse_structure(c, fallback) if c else fallback
    except (json.JSONDecodeError, ValueError, TypeError) as e:
        log.warning("bad structure json: %s", e); return fallback


async def coach(client, url, model, summary: dict, names: tuple[str, ...], syllables: tuple[str, ...]) -> dict:
    c = await _chat(client, url, model, COACH_SYS, json.dumps({"attempt": summary, "names": names, "syllables": syllables}), None, 220)
    try:
        return json.loads(c) if c else {}
    except json.JSONDecodeError:
        return {}
