"""The asan's notebook: Gemini API (cloud, after class) turns session.json into a progress report + tomorrow's lesson."""
from __future__ import annotations

import os
from pathlib import Path

PROMPT = """You are a senior chenda asan reviewing a student's practice log (phrases asked, what Gemma heard them play,
scores, diagnoses). Write in English with Malayalam vaaythari kept as-is: 1) 4-line progress summary with numbers,
2) the two persistent faults and a drill for each, 3) tomorrow's 3-phrase lesson plan with bpm. Under 300 words."""


def report(session_json: Path, model: str) -> str:
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        raise RuntimeError("GEMINI_API_KEY not set")
    from google import genai
    resp = genai.Client(api_key=key).models.generate_content(model=model, contents=[PROMPT, session_json.read_text()])
    return resp.text or ""
