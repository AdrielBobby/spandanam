"""On-device Gemma (via Ollama) = the Asan's brain.

Two jobs only a model can do:
 1. Interpret the *pattern* (which kaalam, who broke pattern) from the strike matrix + a short audio clip
    (Gemma 3n accepts audio natively). DSP tells us tempo; Gemma tells us musical state.
 2. Grade fatigue risk per drummer from fused features and produce a one-line reason for the asan.
Output is strict JSON so haptic commands can be dispatched without parsing prose.
"""
from __future__ import annotations

import base64
import json
import logging
from dataclasses import dataclass

import httpx

from .config import PANCHARI_KAALAMS
from .fatigue import FatigueFeatures
from .sync import NodeTempo

log = logging.getLogger(__name__)

SYSTEM = """You are the Asan (lead) of a Kerala chenda melam. You receive per-drummer telemetry and,
optionally, a 2-second audio clip of the ensemble. Respond ONLY with JSON matching:
{"kaalam": <1-5>, "kaalam_confidence": <0-1>, "transition_imminent": <bool>,
 "drummers": {"<id>": {"pattern_ok": <bool>, "fatigue": "fresh|tiring|risk", "reason": "<=12 words"}},
 "asan_note": "<=20 words in English"}
Rules: 'risk' only if HR slope > +8 bpm/min AND (amp_decay > 25% OR jitter_growth > 60%), or HR > 175.
Panchari melam kaalams: """ + json.dumps(PANCHARI_KAALAMS)


@dataclass(frozen=True)
class CoachDecision:
    kaalam: int
    kaalam_confidence: float
    transition_imminent: bool
    drummers: dict[str, dict]
    asan_note: str
    raw: str

    def rest_commands(self) -> dict[str, str]:
        return {n: "R" for n, d in self.drummers.items() if d.get("fatigue") == "risk"}


def build_prompt(tempos: list[NodeTempo], offsets_ms: dict[str, float],
                 fatigue: list[FatigueFeatures], current_kaalam: int) -> str:
    rows = {
        t.node: {
            "bpm": round(t.bpm, 1), "jitter_ms": round(t.jitter_ms, 1),
            "offset_ms": round(offsets_ms.get(t.node, 0.0), 1),
        } for t in tempos
    }
    for f in fatigue:
        rows.setdefault(f.node, {}).update({
            "hr": round(f.hr_bpm), "hr_slope": round(f.hr_slope_bpm_per_min, 1),
            "amp_decay_pct": round(f.amp_decay_pct, 1), "jitter_growth_pct": round(f.jitter_growth_pct, 1),
        })
    return json.dumps({"current_kaalam": current_kaalam, "drummers": rows})


async def ask_gemma(client: httpx.AsyncClient, url: str, model: str, prompt: str,
                    audio_wav: bytes | None = None) -> CoachDecision | None:
    msg: dict = {"role": "user", "content": prompt}
    if audio_wav:
        msg["audio"] = [base64.b64encode(audio_wav).decode()]   # Ollama multimodal field for gemma3n
    body = {"model": model, "stream": False, "format": "json",
            "messages": [{"role": "system", "content": SYSTEM}, msg],
            "options": {"temperature": 0.1, "num_predict": 300}}
    try:
        r = await client.post(f"{url}/api/chat", json=body, timeout=8.0)
        r.raise_for_status()
        content = r.json()["message"]["content"]
        d = json.loads(content)
        return CoachDecision(int(d.get("kaalam", 1)), float(d.get("kaalam_confidence", 0)),
                             bool(d.get("transition_imminent", False)), dict(d.get("drummers", {})),
                             str(d.get("asan_note", "")), content)
    except (httpx.HTTPError, json.JSONDecodeError, KeyError, ValueError) as e:
        log.warning("gemma call failed: %s", e)
        return None
