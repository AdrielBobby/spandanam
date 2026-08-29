"""Develop and test the Gemma layer without hardware.

  python -m viral.gemma_cli ping                       # is Ollama up, which models
  python -m viral.gemma_cli structure track.mp3        # transcription -> Gemma structure -> Score JSON (saved next to the track)
  python -m viral.gemma_cli structure --fake           # synthetic events, no audio libs needed
  python -m viral.gemma_cli coach                      # fake attempt summary -> coaching
Env: OLLAMA_URL, GEMMA_MODEL
"""
from __future__ import annotations

import argparse
import asyncio
import json
import time
from pathlib import Path

import httpx

from .config import Config
from .gemma_thaalam import coach, default_structure, structure
from .learn import build_score, learn_from_file

FAKE_EVENTS = [(b, c, s) for b, c, s in [
    (0, 0, 1.0), (0.5, 2, .6), (1, 1, .8), (1.5, 2, .5), (2, 0, .9), (2.5, 3, .6), (3, 1, .8), (3.5, 4, .4),
    (4, 0, 1.0), (4.5, 2, .6), (5, 1, .8), (5.5, 2, .5), (6, 0, .9), (6.5, 3, .6), (7, 1, .8), (7.5, 4, .7)]]
FAKE_PROFILE = {0: {"centroid_hz": 140, "count": 4, "mean_strength": .95}, 1: {"centroid_hz": 420, "count": 4, "mean_strength": .8},
                2: {"centroid_hz": 900, "count": 4, "mean_strength": .55}, 3: {"centroid_hz": 1800, "count": 2, "mean_strength": .6},
                4: {"centroid_hz": 4200, "count": 2, "mean_strength": .55}}
FAKE_SUMMARY = {"points": 1420, "accuracy": .62, "perfect": 6, "good": 4, "misses": 4, "wrong_finger": 2, "extra": 1, "notes": 16,
                "stars": 1, "per_finger_miss": [0, 1, 0, 2, 1], "mean_offset_ms": 38}


async def ping(cfg: Config) -> None:
    async with httpx.AsyncClient() as c:
        try:
            r = await c.get(f"{cfg.ollama_url}/api/tags", timeout=5); r.raise_for_status()
            names = [m["name"] for m in r.json().get("models", [])]
            print(f"ollama at {cfg.ollama_url}: {names}"); print("target model:", cfg.gemma_model, "(present)" if cfg.gemma_model in names else "(NOT pulled yet)")
        except Exception as e:
            print(f"ollama NOT reachable at {cfg.ollama_url}: {e}")


async def do_structure(cfg: Config, path: str | None, fake: bool) -> None:
    t0 = time.time()
    if fake or not path:
        fb = default_structure(96, 8)
        async with httpx.AsyncClient() as c:
            st = await structure(c, cfg.ollama_url, cfg.gemma_model, 96, FAKE_PROFILE, FAKE_EVENTS, None, fb)
        sc = build_score(FAKE_EVENTS, st, 96)
    else:
        sc, st = await learn_from_file(Path(path), cfg.ollama_url, cfg.gemma_model)
        Path(path).with_suffix(".score.json").write_text(sc.to_json())
    print(f"[{time.time() - t0:.1f}s] {sc.title} · {sc.thaalam} · cycle {sc.beats_per_cycle} · kit {sc.kit} · {len(sc.notes)} notes")
    print("fingers:", list(zip(sc.finger_map.names, sc.finger_map.syllables)))
    print("phrases:", sc.phrases); print("gemma:", st.notes_en); print(f"evidence ({st.confidence:.2f}):", st.evidence); print("raw:", st.raw[:400])


async def do_coach(cfg: Config) -> None:
    t0 = time.time()
    async with httpx.AsyncClient() as c:
        fb = await coach(c, cfg.ollama_url, cfg.gemma_model, FAKE_SUMMARY, ("thom", "tha", "ki", "ta", "ri"), ("thom", "tha", "ki", "ta", "ri"))
    print(f"[{time.time() - t0:.1f}s]", json.dumps(fb, ensure_ascii=False, indent=1))


def main() -> None:
    ap = argparse.ArgumentParser(); ap.add_argument("cmd", choices=["ping", "structure", "coach"]); ap.add_argument("path", nargs="?")
    ap.add_argument("--fake", action="store_true"); a = ap.parse_args(); cfg = Config()
    asyncio.run({"ping": lambda: ping(cfg), "structure": lambda: do_structure(cfg, a.path, a.fake), "coach": lambda: do_coach(cfg)}[a.cmd]())


if __name__ == "__main__":
    main()
