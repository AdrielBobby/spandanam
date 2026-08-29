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


def clean(text: str) -> str:
    """Strip sentencepiece artifacts Gemma sometimes leaks into JSON strings."""
    return text.replace("\u2581", " ").replace("  ", " ")

STRUCT_SYS = """You are a Kerala percussion asan and music analyst. You receive: estimated bpm, timbre clusters 0-4 (0=lowest/bassiest,
4=brightest) with counts, and quantised events (beat, cluster, strength). Optionally a short audio clip. Decide:
- thaalam: name (e.g. chempada/adi 8, panchari 6, thriputa 7/14, ekam 4, roopakam 6/3, or 'free') and beats_per_cycle
- finger_map: which cluster plays on which finger (thumb..pinky). Bass to thumb, brightest to pinky unless the music says otherwise.
  Give each finger a voice name from the chosen kit and a vaaythari syllable (tha ki ta ka dhi mi dhim thom num ri).
- phrases: 3-6 practice segments as [start_beat, end_beat] of increasing difficulty, aligned to cycles.
- kit: chenda|mridangam|tabla|kit ; title: short; kaalam: 1-3 (tempo stage)
Return ONLY JSON: {"title":"","thaalam":"","beats_per_cycle":8,"kit":"chenda","kaalam":1,
 "finger_map":{"cluster_to_finger":{"0":0,"1":1,"2":2,"3":3,"4":4},"names":["","","","",""],"syllables":["","","","",""]},
 "phrases":[[0,8]], "notes_en":"<=25 words on the rhythm's character"}

Example input: {"bpm": 96, "clusters": {"0": {"centroid_hz": 140, "count": 16}, "1": {"centroid_hz": 420, "count": 16}, "2": {"centroid_hz": 900, "count": 16},
 "3": {"centroid_hz": 1800, "count": 8}, "4": {"centroid_hz": 4200, "count": 8}}, "events": [[0,0,1.0],[0.5,2,0.6],[1,1,0.8],[1.5,2,0.5],[2,0,0.9],[2.5,3,0.6],[3,1,0.8],[3.5,4,0.4], ...]}
Example output: {"title":"Chempada practice","thaalam":"chempada (adi) 8","beats_per_cycle":8,"kit":"chenda","kaalam":1,
 "finger_map":{"cluster_to_finger":{"0":0,"1":1,"2":2,"3":3,"4":4},"names":["valanthala","idanthala-open","idanthala-closed","rim","elathalam"],
 "syllables":["thom","tha","ki","ta","ri"]},"phrases":[[0,8],[0,16],[0,32]],
 "notes_en":"Steady 8-beat chempada: bass on 1 and 5, treble answers on the off-beats, cymbal colour on 4 and 8."}
Rules: cluster 0 is the lowest timbre. Never output a finger index outside 0-4. Keep every key exactly as spelled above."""

COACH_SYS = """You are a warm, precise percussion teacher (a Kerala asan). You receive DETERMINISTIC FACTS about one attempt —
accuracy, weak fingers, weak syllables, dominant error (early/late/wrong_finger/missed), a recommended next bpm and phrase —
plus the finger names/syllables. Do not recompute or contradict the facts: if dominant_error is wrong_finger talk about finger
choice (never about rushing/dragging); if it is late/early talk about timing; if missed, about keeping up. Name the weak fingers
and syllables from the facts. One observation, one physical fix (finger/wrist/breathing), one drill using recommended_phrase and
recommended_bpm. Manglish = Malayalam words in Latin letters mixed with English music terms (use Malayalam, not Kannada/Tamil/Hindi words).
Return ONLY JSON:
{"say_en":"<=30 words","say_ml":"<=30 words of spoken Malayalam written in Latin letters (Manglish), e.g. 'ring finger pathukke, 80 bpm il thudanguka'","drill_phrase":index,"drill_bpm":number,"focus":"timing|finger|dynamics|reward"}"""


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


EXPECTED_KEYS = ("title", "thaalam", "beats_per_cycle", "kit", "kaalam", "finger_map", "phrases", "notes_en",
                 "cluster_to_finger", "names", "syllables", "say_en", "say_ml", "drill_phrase", "drill_bpm", "focus")


def _similar(a: str, b: str) -> bool:
    from difflib import SequenceMatcher
    return SequenceMatcher(a=a.lower(), b=b.lower()).ratio() >= 0.8


def normalize_keys(obj):
    """Small models misspell keys ('kaaalam', 'syllaibles'). Snap any key to the closest expected one, recursively."""
    if isinstance(obj, dict):
        out = {}
        for k, v in obj.items():
            nk = k if k in EXPECTED_KEYS else next((e for e in EXPECTED_KEYS if _similar(k, e)), k)
            out[nk] = normalize_keys(v)
        return out
    if isinstance(obj, list):
        return [normalize_keys(x) for x in obj]
    return obj


def auto_phrases(n_beats: float, cycle: int) -> tuple[tuple[float, float], ...]:
    """Cycle-aligned practice segments of growing length: 1 cycle, 2 cycles, ... up to the whole piece (max 6)."""
    total = max(cycle, int(round(n_beats / cycle)) * cycle)
    out, span = [], cycle
    while span <= total and len(out) < 6:
        out.append((0.0, float(span))); span *= 2
    if not out or out[-1][1] < total:
        out.append((0.0, float(total)))
    return tuple(out[:6])


def parse_structure(content: str, fallback: Structure) -> Structure:
    d = normalize_keys(json.loads(content))
    fm = d.get("finger_map", {})
    c2f = {int(k): int(v) % 5 for k, v in fm.get("cluster_to_finger", {}).items()} or fallback.cluster_to_finger
    kit = d.get("kit") if d.get("kit") in KITS else fallback.kit
    names = tuple((fm.get("names") or KITS[kit]["voices"])[:5]); names = names if len(names) == 5 else tuple(KITS[kit]["voices"])
    syl = tuple((fm.get("syllables") or fallback.syllables)[:5]); syl = syl if len(syl) == 5 else fallback.syllables
    phrases = tuple((float(a), float(b)) for a, b in d.get("phrases", []) if b > a)
    cycle = int(d.get("beats_per_cycle", fallback.beats_per_cycle)) or 8
    if len(phrases) < 2:
        phrases = auto_phrases(max(fallback.phrases[-1][1] if fallback.phrases else cycle, cycle), cycle)
    return Structure(str(d.get("title", fallback.title)), str(d.get("thaalam", fallback.thaalam)),
                     cycle, kit, int(d.get("kaalam", 1)),
                     c2f, names, syl, phrases, str(d.get("notes_en", "")), content)


async def _chat(client: httpx.AsyncClient, url: str, model: str, system: str, user: str, wav: bytes | None, n: int) -> str | None:
    msg: dict = {"role": "user", "content": user}
    if wav:
        msg["audio"] = [base64.b64encode(wav).decode()]
    body = {"model": model, "stream": False, "format": "json", "options": {"temperature": 0.2, "num_predict": n},
            "messages": [{"role": "system", "content": system}, msg]}
    try:
        r = await client.post(f"{url}/api/chat", json=body, timeout=60.0); r.raise_for_status()
        return clean(r.json()["message"]["content"])
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
        return normalize_keys(json.loads(c)) if c else {}
    except json.JSONDecodeError:
        return {}
