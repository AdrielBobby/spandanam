"""Hub entrypoint. Fast path at 100 Hz, Gemma hearing every 2 s, frames to the band."""
from __future__ import annotations

import argparse
import asyncio
import logging
import queue
import time
from pathlib import Path

import httpx
import numpy as np
from rich.live import Live

from . import dsp
from .audio import MicBuffer, open_stream
from .config import HubConfig
from .console import render
from .gemini_report import dump_session
from .gemma_ear import DEFAULT_HEARING, hear
from .haptic import BandLink, compose_frame


log = logging.getLogger("spandanam")


async def run(cfg: HubConfig, preferences: str, session_dir: Path, wav_file: str | None) -> None:
    hop = cfg.sample_rate * cfg.hop_ms // 1000
    q: queue.Queue = queue.Queue(maxsize=200)
    mic = MicBuffer(cfg.sample_rate, cfg.gemma_clip_s)
    if cfg.band_host == "gpio":
        from .pi_band import PiBand
        link = PiBand()
    else:
        link = BandLink(cfg.band_host, cfg.band_port)
    client = httpx.AsyncClient()
    hearing = DEFAULT_HEARING
    running_max: dict[str, float] = {}
    prev_levels: dict[str, float] = {}
    motif_until = 0.0
    last_gemma = 0.0
    events: list[dict] = []
    gemma_task: asyncio.Task | None = None

    if wav_file:
        import soundfile as sf  # optional dev dependency
        data, sr = sf.read(wav_file, dtype="float32")
        data = data.mean(axis=1) if data.ndim > 1 else data
        frames = iter(np.array_split(data, max(1, len(data) // hop)))
        stream = None
    else:
        def cb(indata, _frames, _time, _status):
            try: q.put_nowait(indata[:, 0].copy())
            except queue.Full: pass
        stream = open_stream(cfg.sample_rate, hop, cb); stream.start()

    with Live(refresh_per_second=15) as live:
        while True:
            if wav_file:
                frame = next(frames, None)
                if frame is None: break
                await asyncio.sleep(cfg.hop_ms / 1000)
            else:
                try: frame = q.get(timeout=0.1)
                except queue.Empty: await asyncio.sleep(0); continue
            mic.push(frame)
            energy = dsp.band_energies(frame, cfg.sample_rate)
            levels, running_max = dsp.normalise(energy, running_max)
            onsets = dsp.detect_onsets(levels, prev_levels); prev_levels = levels
            now = time.monotonic()
            motif = hearing.motif if now < motif_until else None
            fb = compose_frame(levels, onsets, hearing.body_map, hearing.gains, motif, cfg.max_intensity)
            link.send(fb)

            if now - last_gemma >= cfg.gemma_clip_s and (gemma_task is None or gemma_task.done()):
                last_gemma = now
                if gemma_task and gemma_task.done() and (h := gemma_task.result()):
                    hearing = h
                    if h.event != "none": motif_until = now + 0.6
                    events.append({"t": now, "hearing": h.raw})
                    if len(events) % 10 == 0: dump_session(session_dir, events)
                stats = {b: round(v, 2) for b, v in levels.items()}
                gemma_task = asyncio.create_task(hear(client, cfg.ollama_url, cfg.gemma_model, mic.wav(), stats, preferences))
            live.update(render(fb, hearing, levels, preferences))
    dump_session(session_dir, events)


def main() -> None:
    ap = argparse.ArgumentParser(description="Spandanam hub")
    ap.add_argument("--band", default=None, help="band IP, or 'gpio' to drive buzzers from Pi GPIO directly")
    ap.add_argument("--prefs", default="default", help="listener preferences, free text (e.g. 'softer chest, more cymbals')")
    ap.add_argument("--wav", default=None, help="play a melam recording instead of the mic")
    ap.add_argument("--session", default=f"data/sessions/{int(time.time())}")
    ap.add_argument("-v", action="store_true")
    a = ap.parse_args()
    logging.basicConfig(level=logging.DEBUG if a.v else logging.INFO)
    cfg = HubConfig(band_host=a.band) if a.band else HubConfig()
    try: asyncio.run(run(cfg, a.prefs, Path(a.session), a.wav))
    except KeyboardInterrupt: pass


if __name__ == "__main__":
    main()
