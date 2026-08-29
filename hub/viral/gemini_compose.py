"""Gemini API (cloud): compose a new percussion piece as a symbolic score -> finger thaalam. Also optional TTS-free 'listen' preview via the sampler."""
from __future__ import annotations

import json
import os

from .score import Score, score_from_dict

PROMPT = """Compose a percussion piece for a 5-finger air-drum glove. Fingers 0..4 = thumb..pinky, thumb = bass voice, pinky = brightest.
Kit: {kit}. Style/brief: {brief}. Thaalam: {thaalam}. Length: {cycles} cycles. BPM: {bpm}.
Make it musical and learnable: repeated motifs, a variation, a kalasham (ending flourish). Include vaaythari syllables per note.
Return ONLY JSON: {{"title":"","bpm":{bpm},"beats_per_cycle":N,"kit":"{kit}","thaalam":"{thaalam}",
 "finger_map":{{"names":["","","","",""],"syllables":["","","","",""]}},
 "notes":[{{"beat":0.0,"finger":0,"velocity":1.0,"label":"thom"}}], "phrases":[[0,8],[8,16]]}}"""


def compose(brief: str, kit: str, thaalam: str, cycles: int, bpm: float, model: str) -> Score:
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        raise RuntimeError("GEMINI_API_KEY not set")
    from google import genai
    client = genai.Client(api_key=key)
    resp = client.models.generate_content(model=model, contents=PROMPT.format(kit=kit, brief=brief, thaalam=thaalam, cycles=cycles, bpm=bpm),
                                          config={"response_mime_type": "application/json"})
    return score_from_dict(json.loads(resp.text or "{}"))
