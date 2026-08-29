"""Post-session report via Gemini API (cloud, never in the live loop)."""
from __future__ import annotations

import json
import os
from pathlib import Path

PROMPT = """You are an accessibility researcher. Given a log of a deaf listener's haptic melam session (Gemma's
per-2s hearings: instruments, kaalam, events, body maps, captions) and the listener's stated preferences, write:
1. A 5-line narrative of the performance as it was felt (kaalam progression, solos, climax).
2. Which body sites carried most information and whether the mapping should change next time.
3. Three concrete improvements to the haptic score. Under 300 words."""


def generate_report(session_json: Path, model: str) -> str:
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        raise RuntimeError("GEMINI_API_KEY not set")
    from google import genai
    client = genai.Client(api_key=key)
    resp = client.models.generate_content(model=model, contents=[PROMPT, session_json.read_text()])
    return resp.text or ""


def dump_session(out_dir: Path, events: list[dict]) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    p = out_dir / "session.json"
    p.write_text(json.dumps(events, ensure_ascii=False, indent=1))
    return p
