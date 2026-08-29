"""Hub entrypoint: asyncio loop tying Sense -> Think -> Act."""
from __future__ import annotations

import argparse
import asyncio
import logging
import time
from collections import deque
from pathlib import Path

import httpx
from rich.live import Live

from . import audio, fatigue, haptics, sync
from .config import HubConfig
from .console import render
from .gemma_coach import ask_gemma, build_prompt
from .gemini_report import dump_session
from .ingest import open_ingest
from .strike import StrikeState, detect_strike

log = logging.getLogger("melam")


async def run(cfg: HubConfig, session_dir: Path, use_audio: bool) -> None:
    queue, transport = await open_ingest(cfg.listen_host, cfg.listen_port)
    strike_state: dict[str, StrikeState] = {}
    strikes: dict[str, deque] = {}            # node -> deque[(t_us, peak_g)]
    hr: dict[str, deque] = {}                 # node -> deque[(t_s, bpm)]
    addr_of: dict[str, tuple[str, int]] = {}
    hstate = haptics.HapticState({})
    events: list[dict] = []
    decision = None
    kaalam = 1
    last_gemma = 0.0
    client = httpx.AsyncClient()
    t0 = time.monotonic()

    def now_s() -> float:
        return time.monotonic() - t0

    def window(dq: deque, seconds: float, key_us: bool) -> list:
        cutoff = (time.monotonic_ns() // 1000 - seconds * 1e6) if key_us else now_s() - seconds
        return [x for x in dq if x[0] >= cutoff]

    with Live(refresh_per_second=8) as live:
        while True:
            # ---- Sense: drain queue
            try:
                s = await asyncio.wait_for(queue.get(), timeout=0.05)
                addr_of[s.node] = s.addr
                st = strike_state.get(s.node, StrikeState())
                st, hit = detect_strike(st, s.t_us, s.accel_mag_g, cfg.strike_threshold_g, cfg.strike_refractory_s)
                strike_state[s.node] = st
                if hit:
                    strikes.setdefault(s.node, deque(maxlen=4000)).append((s.t_us, hit.peak_g))
                if s.bpm > 0:
                    hr.setdefault(s.node, deque(maxlen=4000)).append((now_s(), s.bpm))
            except asyncio.TimeoutError:
                pass

            # ---- Think (DSP, every loop)
            recent = {n: [t for t, _ in dq][-64:] for n, dq in strikes.items()}
            tempos = [sync.tempo_from_strikes(n, ts) for n, ts in recent.items()]
            ref = sync.group_reference(recent)
            offsets = {n: sync.phase_offset_ms(ref, ts) for n, ts in recent.items()}
            feats = {n: fatigue.extract(n, cfg.fatigue_window_s, list(hr.get(n, []))[-60:],
                                        [(t / 1e6, p) for t, p in list(dq)[-120:]])
                     for n, dq in strikes.items()}

            # ---- Think (Gemma, every cfg.gemma_every_s)
            if now_s() - last_gemma >= cfg.gemma_every_s and tempos:
                last_gemma = now_s()
                clip = audio.record_clip() if use_audio else None
                prompt = build_prompt(tempos, offsets, list(feats.values()), kaalam)
                d = await ask_gemma(client, cfg.ollama_url, cfg.gemma_model, prompt, clip)
                if d:
                    decision = d
                    if d.kaalam_confidence > 0.7 and d.kaalam != kaalam:
                        kaalam = d.kaalam
                        for n, a in addr_of.items():
                            await haptics.send(transport, a, cfg.node_port, "K")
                    events.append({"t": now_s(), "prompt": prompt, "decision": d.raw})

            # ---- Act: sync cues + rest commands
            cmds = {n: sync.haptic_cue(o, cfg.phase_tolerance_ms) for n, o in offsets.items()}
            if decision:
                cmds.update(decision.rest_commands())
            for n, c in cmds.items():
                if c and n in addr_of and haptics.should_send(hstate, n, now_s(), 1.5):
                    await haptics.send(transport, addr_of[n], cfg.node_port, c)
                    hstate = haptics.mark_sent(hstate, n, now_s())

            live.update(render(tempos, offsets, feats, decision.drummers if decision else None, kaalam,
                               decision.asan_note if decision else "warming up"))
            if len(events) % 20 == 19:
                dump_session(session_dir, events)


def main() -> None:
    ap = argparse.ArgumentParser(description="Melam Asan hub")
    ap.add_argument("--session", default=f"data/sessions/{int(time.time())}")
    ap.add_argument("--audio", action="store_true", help="feed 2 s mic clips to Gemma 3n")
    ap.add_argument("--model", default=None)
    ap.add_argument("-v", action="store_true")
    a = ap.parse_args()
    logging.basicConfig(level=logging.DEBUG if a.v else logging.INFO)
    cfg = HubConfig(gemma_model=a.model) if a.model else HubConfig()
    try:
        asyncio.run(run(cfg, Path(a.session), a.audio))
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
