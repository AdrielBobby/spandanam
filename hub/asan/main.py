"""Lesson loop: chant + tap the phrase -> listen (mic + stick IMU) -> Gemma hears & judges -> Gemma teaches next drill."""
from __future__ import annotations

import argparse
import asyncio
import json
import logging
import time
from pathlib import Path

import httpx
from rich.console import Console

from . import speech
from .audio import record_clip
from .config import AsanConfig, SEED_PHRASES
from .gemma_asan import Lesson, first_lesson, hear, intent, teach
from .imu import MPU6050Reader
from .pi_band import PiBand
from .vaaythari import Phrase, diff_phrase, tap_schedule

log = logging.getLogger("asan")
con = Console()


def demonstrate(band: PiBand, phrase: Phrase, tap_ms: int) -> None:
    """Asan chants while the wrist buzzers tap each syllable's hand (and the accent)."""
    con.print(f"[bold cyan]Asan:[/] {phrase.text()}  @ {phrase.bpm:.0f} bpm")
    t0 = time.monotonic()
    for tap in tap_schedule(phrase):
        while time.monotonic() - t0 < tap.t_s:
            time.sleep(0.002)
        band.pulse(tap.zone, tap_ms, tap.strength)
    speech.chant(phrase.syllables, phrase.bpm)


async def lesson_loop(cfg: AsanConfig, band: PiBand, imu: MPU6050Reader, session: Path, voice: bool) -> None:
    client = httpx.AsyncClient()
    lesson: Lesson = first_lesson(cfg.start_bpm)
    history: list[dict] = []
    speech.speak(lesson.say_ml if cfg.language == "ml" else lesson.say_en, cfg.language)
    while True:
        phrase = Phrase(lesson.phrase, lesson.bpm)
        demonstrate(band, phrase, cfg.tap_ms)
        con.print("[yellow]Your turn…[/]")
        imu.drain()
        wav = record_clip(phrase.duration_s + cfg.listen_pad_s, cfg.sample_rate)
        strokes = [{"t": round(s.t_s, 3), "g": round(s.peak_g, 1), "tilt": round(s.tilt_deg)} for s in imu.drain()]
        h = await hear(client, cfg.ollama_url, cfg.gemma_model, wav, lesson.phrase, lesson.bpm, strokes) if wav else None
        if h is None:
            con.print("[red]asan didn't hear — retry[/]"); continue
        d = diff_phrase(lesson.phrase, h.played)
        con.print(f"heard: [bold]{'-'.join(h.played) or '—'}[/]  score {h.score}  sim {d.similarity:.2f}  "
                  f"{'rushing ' if h.rushing else ''}{'dragging ' if h.dragging else ''}{'hands! ' if h.hand_confusion else ''}")
        con.print(f"[green]{h.diagnosis_ml}[/]  [dim]{h.diagnosis_en}[/]")
        speech.speak(h.diagnosis_ml if cfg.language == "ml" else h.diagnosis_en, cfg.language)
        for i in h.weak_strokes:                       # haptic pointer to the weak strokes
            if 0 <= i < len(lesson.phrase):
                band.pulse("accent", 120)
        history.append({"asked": lesson.phrase, "bpm": lesson.bpm, "played": h.played, "score": h.score,
                        "diag": h.diagnosis_en, "strokes": len(strokes), "t": time.time()})
        session.mkdir(parents=True, exist_ok=True)
        (session / "session.json").write_text(json.dumps(history, ensure_ascii=False, indent=1))

        if voice:
            con.print("[dim]say something to the asan (2 s) or stay quiet…[/]")
            v = record_clip(2.0, cfg.sample_rate)
            cmd = await intent(client, cfg.ollama_url, cfg.gemma_model, v) if v else {"command": "none"}
            if cmd.get("command") == "stop": break
            if cmd.get("command") == "slower": lesson = Lesson(lesson.phrase, lesson.bpm * 0.8, cmd.get("reply_ml", ""), "", "tempo"); speech.speak(lesson.say_ml); continue
            if cmd.get("command") == "faster": lesson = Lesson(lesson.phrase, min(200, lesson.bpm * 1.15), cmd.get("reply_ml", ""), "", "tempo"); speech.speak(lesson.say_ml); continue
            if cmd.get("command") == "repeat": continue
            if cmd.get("command") == "teach" and cmd.get("phrase_name") in SEED_PHRASES:
                lesson = Lesson(tuple(SEED_PHRASES[cmd["phrase_name"]]), cfg.start_bpm, cmd.get("reply_ml", ""), "", "new_phrase"); speech.speak(lesson.say_ml); continue

        lesson = await teach(client, cfg.ollama_url, cfg.gemma_model, history, lesson)
        con.print(f"[magenta]next:[/] {'-'.join(lesson.phrase)} @ {lesson.bpm:.0f}  ({lesson.focus})  {lesson.say_ml}")
        speech.speak(lesson.say_ml if cfg.language == "ml" else lesson.say_en, cfg.language)


def main() -> None:
    ap = argparse.ArgumentParser(description="Vaaythari — Gemma chenda asan")
    ap.add_argument("--dry", action="store_true", help="no GPIO/I2C (laptop dev)")
    ap.add_argument("--voice", action="store_true", help="let the student talk to the asan between attempts")
    ap.add_argument("--model", default=None); ap.add_argument("--bpm", type=float, default=None)
    ap.add_argument("--lang", default="ml", choices=["ml", "en"])
    ap.add_argument("--session", default=f"data/sessions/{int(time.time())}"); ap.add_argument("-v", action="store_true")
    a = ap.parse_args()
    logging.basicConfig(level=logging.DEBUG if a.v else logging.WARNING)
    cfg = AsanConfig(**{k: v for k, v in {"gemma_model": a.model, "start_bpm": a.bpm, "language": a.lang}.items() if v})
    band = PiBand(dry_run=a.dry); imu = MPU6050Reader(cfg.imu_strike_g, dry_run=a.dry); imu.start()
    try: asyncio.run(lesson_loop(cfg, band, imu, Path(a.session), a.voice))
    except KeyboardInterrupt: pass
    finally: band.off()


if __name__ == "__main__":
    main()
