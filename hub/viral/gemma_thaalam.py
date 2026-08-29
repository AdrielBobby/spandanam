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
from .transcribe import digest

log = logging.getLogger(__name__)


def clean(text: str) -> str:
    """Strip sentencepiece artifacts Gemma sometimes leaks into JSON strings."""
    return text.replace("\u2581", " ").replace("  ", " ")


def repair_json(text: str) -> str:
    """Best-effort repair for small-model JSON: strip code fences/prose, drop trailing commas, close truncated brackets/strings."""
    t = text.strip()
    if "```" in t:
        t = t.split("```")[1] if t.count("```") >= 2 else t.replace("```", "")
        t = t[4:] if t.startswith("json") else t
    start = t.find("{")
    if start > 0:
        t = t[start:]
    try:
        json.loads(t); return t
    except json.JSONDecodeError:
        pass
    # cut back to the last complete value, then balance
    import re
    t = re.sub(r",\s*([}\]])", r"\1", t)                      # trailing commas
    if t.count('"') % 2 == 1:
        t = t[: t.rfind('"')]                                    # unterminated string
    t = re.sub(r",\s*\"[^\"]*\"?\s*:?\s*$", "", t)             # dangling key
    t = t.rstrip(", \n\t:")
    stack = []
    for ch in t:
        if ch in "{[": stack.append("}" if ch == "{" else "]")
        elif ch in "}]" and stack and stack[-1] == ch: stack.pop()
    t += "".join(reversed(stack))
    try:
        json.loads(t); return t
    except json.JSONDecodeError:
        return text

STRUCT_SYS = """You are a Kerala percussion ashaan and music analyst. You receive a DIGEST of a recording: bpm, timbre clusters 0-4
(0=lowest/bassiest, 4=brightest) with counts, periodicity scores for candidate cycle lengths (higher = the pattern repeats at that
many beats), a per-cluster beat histogram, and the opening pattern as "beat:cluster". Optionally a short audio clip. Decide:
- thaalam: name (e.g. chempada/adi 8, panchari 6, thriputa 7/14, ekam 4, roopakam 6/3, or 'free') and beats_per_cycle
- finger_map: which cluster plays on which finger (thumb..pinky). Bass to thumb, brightest to pinky unless the music says otherwise.
  Give each finger a voice name from the chosen kit and a vaaythari syllable (tha ki ta ka dhi mi dhim thom num ri).
- phrases: 3-6 practice segments as [start_beat, end_beat] of increasing difficulty, aligned to cycles.
- kit: chenda|mridangam|tabla|kit ; title: short; kaalam: 1-3 (tempo stage)
Return ONLY JSON: {"title":"","thaalam":"","beats_per_cycle":8,"kit":"chenda","kaalam":1,
 "finger_map":{"cluster_to_finger":{"0":0,"1":1,"2":2,"3":3,"4":4},"names":["","","","",""],"syllables":["","","","",""]},
 "phrases":[[0,8]], "notes_en":"<=25 words on the rhythm's character",
 "evidence":"<=20 words: which periodicity/histogram numbers led to beats_per_cycle", "confidence":0-1}

Never copy sample text; every value must come from THIS digest. Names must be the chosen kit's voices in low→high order
(chenda: valanthala, idanthala-open, idanthala-closed, rim, elathalam; mridangam: thom, nam, dhin, chapu, arai; tabla: ge, na, tin, te, ke).
Rules: cluster 0 is the lowest timbre. Never output a finger index outside 0-4. Keep every key exactly as spelled above.
Thaalam hints: thakita practice = 3; panchari = 6 (pathikaalam very slow, later kaalams double); pandi = 7 (often felt as 14);
chempada/adi = 8; ekam = 4; khanda = 5; thriputa = 7; roopakam = 3/6. Use cycle_periodicity (also by half/double tempo) + beat_histogram as evidence; if evidence_strength is weak or very weak, say so in
"evidence", keep confidence <= 0.5 and prefer best_cycle_guess. Do not claim certainty the numbers don't support.
DO NOT list or echo the events. Output ONLY the small JSON object described — nothing else."""

COACH_SYS = """You are a warm, precise percussion teacher (a Kerala ashaan). You receive DETERMINISTIC FACTS about one attempt —
accuracy, weak fingers, weak syllables, dominant error (early/late/wrong_finger/missed), a recommended next bpm and phrase —
plus the finger names/syllables. Do not recompute or contradict the facts: if dominant_error is wrong_finger talk about finger
choice (never about rushing/dragging); if it is late/early talk about timing; if missed, about keeping up. Name the weak fingers
and syllables from the facts. One observation, one physical fix (finger/wrist/breathing), one drill using recommended_phrase and
recommended_bpm. Manglish = Malayalam words in Latin letters mixed with English music terms (use Malayalam, not Kannada/Tamil/Hindi words).
Manglish examples of the tone we want (do not copy, adapt to the facts):
 - "Ring finger konjam late aanu, 'ka' il. Wrist relax cheyyu. Phrase 2, 72 bpm il onnu koode."
 - "Kollam! Timing sheri aayi. Ippo 'thom' il shakthi kooti, phrase 3, 90 bpm."
 - "Middle finger 'ta' miss aavunnu. Slow aayi thudanguka — 60 bpm, phrase 1."
Return ONLY JSON:
{"say_en":"<=30 words","say_ml":"<=30 words Manglish like the examples","drill_phrase":index,"drill_bpm":number,"focus":"timing|finger|dynamics|reward"}"""


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
    evidence: str = ""
    confidence: float = 0.0


def default_structure(bpm_hint: float, n_beats: float) -> Structure:
    return Structure("untitled", "chempada (8)", 8, "chenda", 1, {i: i for i in range(5)},
                     tuple(KITS["chenda"]["voices"]), ("thom", "tha", "ki", "ta", "ri"),
                     tuple((float(s), float(min(s + 8, n_beats))) for s in range(0, int(n_beats), 8))[:6] or ((0.0, 8.0),),
                     "default mapping", "{}")


EXPECTED_KEYS = ("title", "thaalam", "beats_per_cycle", "kit", "kaalam", "finger_map", "phrases", "notes_en",
                 "cluster_to_finger", "names", "syllables", "say_en", "say_ml", "drill_phrase", "drill_bpm", "focus",
                 "phrase", "bpm", "banter", "evidence", "confidence")


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
    names_for_cycle = {3: "thakita/roopakam (3)", 4: "ekam (4)", 5: "khanda (5)", 6: "panchari (6)", 7: "thriputa/pandi (7)", 8: "chempada/adi (8)", 12: "panchari (12)", 14: "pandi (14)", 16: "chempada (16)"}
    thaalam = str(d.get("thaalam") or "").strip() or names_for_cycle.get(cycle, f"{cycle}-beat cycle")
    return Structure(str(d.get("title") or fallback.title), thaalam,
                     cycle, kit, int(d.get("kaalam", 1)),
                     c2f, names, syl, phrases, str(d.get("notes_en", "")), content,
                     str(d.get("evidence", "")), float(min(1.0, max(0.0, d.get("confidence", 0.5)))))


async def _chat(client: httpx.AsyncClient, url: str, model: str, system: str, user: str, wav: bytes | None, n: int,
                timeout: float = 60.0) -> str | None:
    msg: dict = {"role": "user", "content": user}
    if wav:
        msg["audio"] = [base64.b64encode(wav).decode()]
    body = {"model": model, "stream": False, "format": "json", "options": {"temperature": 0.2, "num_predict": n},
            "messages": [{"role": "system", "content": system}, msg]}
    try:
        r = await client.post(f"{url}/api/chat", json=body, timeout=timeout); r.raise_for_status()
        return repair_json(clean(r.json()["message"]["content"]))
    except (httpx.HTTPError, KeyError) as e:
        log.warning("gemma failed: %s", e); return None


async def structure(client, url, model, bpm: float, profile: dict, events: list[tuple[float, int, float]],
                    wav: bytes | None, fallback: Structure, scores: dict[int, float] | None = None) -> Structure:
    dg = digest(bpm, profile, events, scores=scores)
    guess = int(dg["best_cycle_guess"])
    user = (json.dumps({"digest": dg, "fingers": FINGERS}) +
            f'\nFill exactly this JSON (no events, no extra keys). beats_per_cycle defaults to the evidence-based guess {guess} unless you '
            f'have a musical reason: {{"title":"","thaalam":"","beats_per_cycle":{guess},"kit":"chenda","kaalam":1,'
            '"finger_map":{"cluster_to_finger":{"0":0,"1":1,"2":2,"3":3,"4":4},"names":["","","","",""],"syllables":["","","","",""]},'
            f'"phrases":[[0,{guess}]],"notes_en":"","evidence":"","confidence":0.5}}')
    c = await _chat(client, url, model, STRUCT_SYS, user, wav, 450)
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
