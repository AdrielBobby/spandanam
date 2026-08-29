"""Gemma 3n on-device = the Asan.

hear():   audio of the student's attempt (+ IMU strokes) -> syllables actually played, per-stroke quality, diagnosis
teach():  history of attempts -> the next phrase (may be new), tempo, one-line Malayalam correction, focus
intent(): student's spoken request (audio) -> command (slower / repeat / teach X / stop)
All strict JSON. Nothing here needs the internet.
"""
from __future__ import annotations

import base64
import json
import logging
from dataclasses import dataclass, field

import httpx

from .config import SEED_PHRASES, SYLLABLES
from .vaaythari import validate_syllables

log = logging.getLogger(__name__)

SYL_LIST = ", ".join(SYLLABLES)

HEAR_SYS = f"""You are a chenda asan (master drummer-teacher) in Kerala. You hear a short clip of a student playing a
vaaythari phrase on a chenda (or practice surface). Stick IMU strokes (time, peak g, tilt) are given as hints.
Transcribe what was PLAYED as syllables from: {SYL_LIST}. Then judge it against what was ASKED.
Return ONLY JSON: {{"played": ["..."], "tempo_ok": true|false, "rushing": true|false, "dragging": true|false,
 "weak_strokes": [indices], "hand_confusion": true|false, "diagnosis_en": "<=15 words", "diagnosis_ml": "<=15 words Malayalam",
 "score": 0-100}}"""

TEACH_SYS = f"""You are a patient chenda asan. Given the lesson history (phrases asked, what was played, scores, diagnoses),
decide the next drill. Compose vaaythari ONLY from syllables: {SYL_LIST}. Rules: if score<60 repeat same phrase slower
(bpm*0.8); if left/right confusion, isolate that hand (e.g. ta ta ta / ka ka ka); if score>85 twice, extend the phrase
or raise bpm*1.15 (max 200). Occasionally compose a NEW phrase in the Panchari idiom (dhim tha ka combinations).
Return ONLY JSON: {{"phrase": ["..."], "bpm": number, "say_ml": "<=20 words Malayalam, warm, specific",
 "say_en": "<=20 words", "focus": "tempo|left_hand|right_hand|accent|new_phrase|reward"}}"""

INTENT_SYS = """The student speaks (Malayalam or English) to their chenda asan. Map to a command.
Return ONLY JSON: {"command": "slower|faster|repeat|teach|stop|none", "phrase_name": "thakita|thakadhimi|dhimthakathakita|null",
 "reply_ml": "<=10 words"}"""


@dataclass(frozen=True)
class Hearing:
    played: tuple[str, ...]
    tempo_ok: bool
    rushing: bool
    dragging: bool
    weak_strokes: tuple[int, ...]
    hand_confusion: bool
    diagnosis_en: str
    diagnosis_ml: str
    score: int
    raw: str = "{}"


@dataclass(frozen=True)
class Lesson:
    phrase: tuple[str, ...]
    bpm: float
    say_ml: str
    say_en: str
    focus: str
    raw: str = "{}"


def parse_hearing(content: str) -> Hearing:
    d = json.loads(content)
    return Hearing(validate_syllables(list(d.get("played", []))), bool(d.get("tempo_ok", False)),
                   bool(d.get("rushing", False)), bool(d.get("dragging", False)),
                   tuple(int(i) for i in d.get("weak_strokes", [])), bool(d.get("hand_confusion", False)),
                   str(d.get("diagnosis_en", "")), str(d.get("diagnosis_ml", "")),
                   int(min(100, max(0, d.get("score", 0)))), content)


def parse_lesson(content: str, fallback: Lesson) -> Lesson:
    d = json.loads(content)
    phrase = validate_syllables(list(d.get("phrase", []))) or fallback.phrase
    bpm = float(min(200, max(30, d.get("bpm", fallback.bpm))))
    return Lesson(phrase, bpm, str(d.get("say_ml", "")), str(d.get("say_en", "")), str(d.get("focus", "tempo")), content)


def first_lesson(bpm: float) -> Lesson:
    return Lesson(tuple(SEED_PHRASES["thakita"]), bpm, "നമുക്ക് തകിട തുടങ്ങാം", "Let's start with thakita", "new_phrase")


async def _chat(client: httpx.AsyncClient, url: str, model: str, system: str, user: str,
                wav: bytes | None, max_tokens: int) -> str | None:
    msg: dict = {"role": "user", "content": user}
    if wav:
        msg["audio"] = [base64.b64encode(wav).decode()]
    body = {"model": model, "stream": False, "format": "json", "options": {"temperature": 0.3, "num_predict": max_tokens},
            "messages": [{"role": "system", "content": system}, msg]}
    try:
        r = await client.post(f"{url}/api/chat", json=body, timeout=30.0)
        r.raise_for_status()
        return r.json()["message"]["content"]
    except (httpx.HTTPError, KeyError) as e:
        log.warning("gemma failed: %s", e)
        return None


async def hear(client, url, model, wav: bytes, asked: tuple[str, ...], bpm: float, strokes: list[dict]) -> Hearing | None:
    user = json.dumps({"asked": list(asked), "bpm": bpm, "imu_strokes": strokes})
    c = await _chat(client, url, model, HEAR_SYS, user, wav, 300)
    try:
        return parse_hearing(c) if c else None
    except (json.JSONDecodeError, ValueError) as e:
        log.warning("bad hearing json: %s", e); return None


async def teach(client, url, model, history: list[dict], current: Lesson) -> Lesson:
    c = await _chat(client, url, model, TEACH_SYS, json.dumps({"history": history[-6:], "current": {"phrase": current.phrase, "bpm": current.bpm}}), None, 250)
    try:
        return parse_lesson(c, current) if c else current
    except (json.JSONDecodeError, ValueError):
        return current


async def intent(client, url, model, wav: bytes) -> dict:
    c = await _chat(client, url, model, INTENT_SYS, "student speaks", wav, 120)
    try:
        return json.loads(c) if c else {"command": "none"}
    except json.JSONDecodeError:
        return {"command": "none"}
