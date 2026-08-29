"""Post-session multimodal report via Gemini API (cloud). Never in the real-time loop."""
from __future__ import annotations

import json
import logging
import os
from pathlib import Path

log = logging.getLogger(__name__)

PROMPT = """You are a chenda melam coach. Given a session telemetry JSON (per-drummer tempo, phase offsets,
fatigue features, Gemma's on-device decisions over time) and optionally a video, write:
1. A 5-line group summary (sync quality, kaalam transitions, safety events).
2. Per-drummer coaching: one strength, one fix, one drill.
3. A safety note for the asan (who should rest first next time and why).
Keep it under 350 words. Be specific with numbers from the data."""


def generate_report(session_json: Path, video: Path | None, model: str) -> str:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY not set")
    from google import genai  # lazy: hub must run fully offline without this

    client = genai.Client(api_key=api_key)
    parts: list = [PROMPT, session_json.read_text()]
    if video and video.exists():
        parts.append(client.files.upload(file=str(video)))
    resp = client.models.generate_content(model=model, contents=parts)
    return resp.text or ""


def save_report(out_dir: Path, text: str) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    p = out_dir / "report.md"
    p.write_text(text)
    log.info("report written to %s", p)
    return p


def dump_session(out_dir: Path, events: list[dict]) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    p = out_dir / "session.json"
    p.write_text(json.dumps(events, indent=1))
    return p
