"""Thaalam server: FastAPI + WebSocket dashboard. Modes: free (metronome on fingers), learn (upload -> Gemma -> score),
practice (Yousician-style real-time judging), compose (Gemini)."""
from __future__ import annotations

import asyncio
import json
import logging
import mimetypes
import time
from pathlib import Path

import httpx
from fastapi import FastAPI, File, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from . import judge
from .config import FINGER_KEYS, INPUT_OFFSET_MS, KITS, Config
from .events import Strike
from .bridge import analysis_for_coach, analyze_attempt, phrase_to_score
from .gemma_game import next_round
from .gemma_thaalam import coach
from .gemini_compose import compose
from .gemma_compose import compose_gemma
from .hardware import Glove
from .imu import MPU6050Reader, Stroke
from .ladder import DEFAULT_SCALES, Ladder, advance
from .learn import learn_from_file
from .malayalam import LABELS_ML, coach_ml, structure_ml
from .metronome import run_metronome
from .motion import motion_feedback
from .score import Score, score_from_dict
from .sound import Sampler
from . import speech

log = logging.getLogger("viral")
ROOT = Path(__file__).parent
ASSETS = ROOT.parents[1] / "assets"
TRACKS = ASSETS / "tracks"


def chantable_syllables(sc: Score) -> tuple[str, ...]:
    """sc's vaaythari syllables in note order; drops unlabeled notes (learn/compose scores may lack real syllables)."""
    return tuple(n.label for n in sc.notes if n.label)


class Hub:
    def __init__(self, cfg: Config):
        self.cfg = cfg
        self.glove = Glove(cfg.dry)
        self.sampler = Sampler("chenda")
        self.imu = MPU6050Reader(cfg.imu_strike_g, dry_run=cfg.dry); self.imu.start()
        self.clients: set[WebSocket] = set()
        self.mode = "free"; self.bpm = 90.0; self.cycle = 8; self.click_mode = "walk"
        self.score: Score | None = None
        self.play: judge.PlayState | None = None
        self.ladder: Ladder | None = None
        self.round_strokes: list[Stroke] = []
        self.stop_metro = asyncio.Event(); self.metro_task: asyncio.Task | None = None
        self.http = httpx.AsyncClient()
        self.last_summary: dict = {}
        self.game_level = 0; self.game_history: list[dict] = []
        self.karaoke = False                                     # vaaythari chant is opt-in (toggle in the dashboard)
        # Gemma engines: primary from config; extras from GEMMA_ENGINES (e.g. laptop e4b over tunnel + on-Pi 1b)
        # With named engines configured, they ARE the list; otherwise the single configured Gemma is "primary".
        self.engines: dict[str, dict] = dict(cfg.gemma_engines) or {"primary": {"url": cfg.ollama_url, "model": cfg.gemma_model}}
        self.engine_mode: str = next(iter(self.engines))                    # an engine name, or "both"

    async def broadcast(self, msg: dict) -> None:
        dead = []
        for ws in list(self.clients):
            try: await ws.send_text(json.dumps(msg, ensure_ascii=False))
            except Exception: dead.append(ws)
        for ws in dead: self.clients.discard(ws)

    # ---- inputs
    async def on_strike(self, s: Strike) -> None:
        self.sampler.play(s.finger, s.velocity)
        self.glove.cue(s.finger, ms=25, led=True)                    # tactile confirmation
        msg = {"type": "strike", "finger": s.finger, "v": s.velocity, "src": s.source}
        if self.mode == "practice" and self.score and self.play:
            self.play, j = judge.judge_strike(self.score, self.play, s)
            msg |= {"judge": j.verdict, "offset_ms": round(j.offset_ms), "note": j.note_index, "streak": self.play.streak, "points": self.play.points}
        await self.broadcast(msg)

    async def poll_imu(self) -> None:
        while True:
            for st in self.imu.drain():
                if self.mode == "practice": self.round_strokes.append(st)   # motion coach: tilt at impact
                await self.on_strike(Strike(0, time.monotonic(), min(1.0, st.peak_g / 8), "imu"))
            await asyncio.sleep(0.005)

    # ---- free mode
    async def start_free(self) -> None:
        await self.stop_all(); self.mode = "free"; self.stop_metro = asyncio.Event()
        def click(c):
            self.glove.cue(c.finger, ms=40 if not c.downbeat else 90, led=c.downbeat)
            asyncio.get_event_loop().create_task(self.broadcast({"type": "click", "beat": c.beat, "finger": c.finger, "down": c.downbeat}))
        self.metro_task = asyncio.create_task(run_metronome(self.bpm, self.cycle, self.click_mode, click, self.stop_metro))

    async def stop_all(self) -> None:
        self.stop_metro.set()
        if self.metro_task: self.metro_task.cancel(); self.metro_task = None
        self.play = None; self.glove.all_off()
        if self.mode in ("listen", "practice"): self.mode = "idle"      # _listen_loop / _practice_loop check this and exit
        speech.stop()                                                      # kill any chant/speech immediately
        try:
            self.sampler.stop()
        except Exception: pass

    # ---- listen mode: auto-play the score (speaker + LEDs) while the lanes fall, no judging
    async def start_listen(self, phrase: int | None, bpm_scale: float = 1.0) -> None:
        if not self.score: return
        await self.stop_all(); self.mode = "listen"
        sc = self.score
        if phrase is not None and 0 <= phrase < len(sc.phrases):
            a, b = sc.phrases[phrase]; sc = sc.slice(a, b)
        sc = Score(sc.title, sc.bpm * bpm_scale, sc.beats_per_cycle, sc.notes, sc.finger_map, sc.kit, sc.thaalam, sc.phrases)
        self.sampler.set_kit(sc.kit)
        lead_in = 2 * sc.beat_s; start = time.monotonic() + lead_in
        await self.broadcast({"type": "practice_start", "score": json.loads(sc.to_json()), "lead_in_s": lead_in, "listen": True})
        self._chant(sc)
        asyncio.create_task(self._listen_loop(sc, start))

    async def _listen_loop(self, sc: Score, start: float) -> None:
        for i, n in enumerate(sc.notes):
            if self.mode != "listen": return
            await asyncio.sleep(max(0.0, start + n.beat * sc.beat_s - time.monotonic()))
            self.sampler.play(n.finger, n.velocity); self.glove.cue(n.finger, ms=40, led=True)
            await self.broadcast({"type": "strike", "finger": n.finger, "v": n.velocity, "src": "listen", "note": i, "judge": "auto"})
        await asyncio.sleep(0.5)
        if self.mode == "listen":
            self.mode = "idle"; await self.broadcast({"type": "status", "text": "listen finished — your turn: Practice"})

    # ---- practice mode
    async def start_practice(self, phrase: int | None, bpm_scale: float = 1.0) -> None:
        if not self.score: return
        await self.stop_all(); self.mode = "practice"
        sc = self.score
        if phrase is not None and 0 <= phrase < len(sc.phrases):
            a, b = sc.phrases[phrase]; sc = sc.slice(a, b)
        sc = Score(sc.title, sc.bpm * bpm_scale, sc.beats_per_cycle, sc.notes, sc.finger_map, sc.kit, sc.thaalam, sc.phrases)
        self.sampler.set_kit(sc.kit)
        lead_in = 4 * sc.beat_s
        start = time.monotonic() + lead_in
        self.play = judge.PlayState(start_s=start)
        self.round_strokes = []
        await self.broadcast({"type": "practice_start", "score": json.loads(sc.to_json()), "lead_in_s": lead_in})
        self._chant(sc)
        asyncio.create_task(self._practice_loop(sc))

    # ---- kaalam ladder: practice the same phrase up through a sequence of tempo
    # steps, auto-advancing (or retrying) after each round -- see _practice_loop.
    async def start_ladder(self, phrase: int | None, scales: tuple[float, ...] = DEFAULT_SCALES) -> None:
        if not self.score: return
        self.ladder = Ladder(scales, phrase, 0)
        await self.broadcast({"type": "ladder_start", "total_steps": self.ladder.total_steps, "bpm_scale": self.ladder.bpm_scale})
        await self.start_practice(phrase, self.ladder.bpm_scale)

    async def _practice_loop(self, sc: Score) -> None:
        if self.play is None: return          # stop_all() raced us before our first turn on the event loop
        cued: set[int] = set()
        end = self.play.start_s + sc.length_beats * sc.beat_s + 0.3
        for b in range(4):                                               # count-in on thumb
            if self.play is None: return       # stop_all() landed mid-count-in
            await asyncio.sleep(max(0, self.play.start_s - (4 - b) * sc.beat_s - time.monotonic())); self.glove.cue(0, 40, led=True)
        while self.mode == "practice" and self.play and time.monotonic() < end:
            now = time.monotonic()
            for i in judge.upcoming(sc, self.play, now, 0.12):          # LED + buzz ~120 ms before the note
                if i not in cued:
                    cued.add(i); self.glove.cue(sc.notes[i].finger, ms=50, led=True)
            self.play, missed = judge.sweep_misses(sc, self.play, now)
            if missed: await self.broadcast({"type": "miss", "notes": missed, "streak": 0})
            await asyncio.sleep(0.01)
        if self.play:
            self.last_summary = judge.summary(sc, self.play) | {"per_finger_miss": self._per_finger(sc)}
            mf = motion_feedback(self.round_strokes)
            if mf: self.last_summary |= {"motion": mf.as_dict()}
            analysis = analyze_attempt(sc, self.play.log)
            if analysis:
                self.last_summary |= {"analysis": analysis.as_dict()}
            await self.broadcast({"type": "practice_end", "summary": self.last_summary})
            asyncio.create_task(self._coach_after(sc, analysis))   # coaching (7–15 s of Gemma) never blocks the round flow
            if self.ladder:                                          # kaalam ladder (Adriel): step up / retry, next round starts itself
                prev, result = self.ladder, advance(self.ladder, self.last_summary["stars"])
                self.ladder = result.ladder
                await self.broadcast({"type": f"ladder_{result.event}", "total_steps": prev.total_steps,
                                       "step": self.ladder.step if self.ladder else None,
                                       "bpm_scale": self.ladder.bpm_scale if self.ladder else None})
                if self.ladder:
                    await self.start_practice(self.ladder.phrase, self.ladder.bpm_scale)
                    return
        self.mode = "idle"
        return

    def active_engines(self) -> list[str]:
        if self.engine_mode == "both":
            return list(self.engines)
        return [self.engine_mode if self.engine_mode in self.engines else next(iter(self.engines))]

    def engine(self, name: str | None = None) -> dict:
        e = self.engines.get(name or self.active_engines()[0], next(iter(self.engines.values())))
        return e | {"name": name or self.active_engines()[0], "on_device": ("127.0.0.1" in e["url"] and ":11435" not in e["url"])}

    async def _coach_one(self, name: str, facts: dict, sc: Score, analysis) -> dict:
        e = self.engine(name); t0 = time.monotonic()
        fb = await coach(self.http, e["url"], e["model"], facts, sc.finger_map.names, sc.finger_map.syllables)
        if analysis:                                             # accurate Malayalam from facts; Gemma's Manglish kept separately
            ml = coach_ml(analysis.accepted_accuracy_pct, analysis.dominant_error, list(analysis.weak_fingers),
                          list(analysis.weak_bols), fb.get("drill_bpm") or analysis.recommended_tempo_bpm, fb.get("drill_phrase"))
            fb = {**fb, "say_manglish": fb.get("say_ml", ""), "say_ml": ml}
        return {**fb, "engine": name, "model": e["model"], "on_device": e["on_device"], "seconds": round(time.monotonic() - t0, 1)}

    async def _coach_after(self, sc: Score, analysis) -> None:
        """Gemma coaching runs after the round has ended so the UI shows stars immediately. In 'both' mode every engine answers."""
        try:
            facts = (analysis_for_coach(analysis, sc.bpm) | {"points": self.last_summary["points"], "stars": self.last_summary["stars"]}) if analysis else self.last_summary
            results = await asyncio.gather(*[self._coach_one(n, facts, sc, analysis) for n in self.active_engines()], return_exceptions=True)
            ok = [r for r in results if isinstance(r, dict)]
            for r in results:
                if not isinstance(r, dict): log.warning("coach engine failed: %s", r)
            if not ok: return
            await self.broadcast({"type": "coach", **ok[0], "results": ok, "mode": self.engine_mode})
        except Exception as e:
            log.warning("coach failed: %s", e)

    def _per_finger(self, sc: Score) -> list[int]:
        return [sum(1 for n in sc.notes if n.finger == f) for f in range(5)]

    def _chant(self, sc: Score) -> None:
        """Fire-and-forget the vaaythari chant (only when karaoke is on); speech.chant() blocks on a subprocess, so it runs off the loop."""
        if not self.karaoke:
            return
        syllables = chantable_syllables(sc)
        if syllables:
            asyncio.get_running_loop().run_in_executor(None, speech.chant, syllables, sc.bpm)


def create_app(cfg: Config) -> FastAPI:
    app = FastAPI(title="Thaalam"); hub = Hub(cfg)
    app.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")
    mimetypes.add_type("model/gltf-binary", ".glb")
    ASSETS.mkdir(parents=True, exist_ok=True)
    app.mount("/assets", StaticFiles(directory=ASSETS), name="assets")

    @app.on_event("startup")
    async def _up(): asyncio.create_task(hub.poll_imu()); await hub.start_free()

    @app.get("/")
    async def index(): return FileResponse(ROOT / "static" / "index.html")

    @app.get("/api/state")
    async def state():
        return {"mode": hub.mode, "bpm": hub.bpm, "cycle": hub.cycle, "kit": hub.sampler.kit, "kits": KITS, "keys": FINGER_KEYS, "labels_ml": LABELS_ML,
                "audio_device": getattr(hub.sampler.mixer, "device_name", None), "karaoke": hub.karaoke,
                "gemma": {"model": hub.engine()["model"], "ollama_url": hub.engine()["url"], "gemini_model": cfg.gemini_model,
                          "mode": hub.engine_mode, "engines": {n: hub.engine(n) for n in hub.engines}},
                "score": json.loads(hub.score.to_json()) if hub.score else None, "dry": cfg.dry}

    async def _engine_status(name: str) -> dict:
        e = hub.engine(name)
        try:
            tags = (await hub.http.get(f"{e['url']}/api/tags", timeout=4)).json().get("models", [])
            ps = (await hub.http.get(f"{e['url']}/api/ps", timeout=4)).json().get("models", [])
            return {"engine": name, "ok": True, "model": e["model"], "ollama_url": e["url"], "on_device": e["on_device"],
                    "available": [m["name"] for m in tags], "loaded": [m["name"] for m in ps], "present": e["model"] in [m["name"] for m in tags]}
        except Exception as ex:
            return {"engine": name, "ok": False, "model": e["model"], "ollama_url": e["url"], "on_device": e["on_device"], "error": str(ex)[:120]}

    @app.get("/api/gemma")
    async def gemma_status():
        """Proof-of-life for judges: every Gemma engine — which model, where, up, loaded — and which is active."""
        statuses = await asyncio.gather(*[_engine_status(n) for n in hub.engines])
        active = hub.active_engines()
        primary = next(s for s in statuses if s["engine"] == active[0])
        return {**primary, "mode": hub.engine_mode, "active": active, "engines": statuses}

    @app.post("/api/gemma/select")
    async def gemma_select(body: dict):
        mode = str(body.get("mode", "primary"))
        if mode != "both" and mode not in hub.engines:
            return JSONResponse({"ok": False, "error": f"unknown engine {mode}; have {list(hub.engines)} or 'both'"}, 400)
        hub.engine_mode = mode
        await hub.broadcast({"type": "status", "text": f"Gemma engine → {mode}"})
        return {"ok": True, "mode": mode, "active": hub.active_engines()}

    @app.post("/api/audio/reopen")
    async def audio_reopen():
        """Rebind audio to the current default output device (after plugging in headphones / the stage speaker)."""
        try:
            hub.sampler.mixer.reopen(); name = hub.sampler.mixer.device_name
        except Exception as e:
            return JSONResponse({"ok": False, "error": str(e)}, 500)
        hub.sampler.play(0, 0.6)                                     # audible confirmation
        await hub.broadcast({"type": "status", "text": f"audio → {name}"})
        return {"ok": True, "audio_device": name}

    @app.post("/api/learn")
    async def learn(file: UploadFile = File(...)):
        TRACKS.mkdir(parents=True, exist_ok=True); p = TRACKS / file.filename
        p.write_bytes(await file.read())
        await hub.broadcast({"type": "status", "text": "transcribing…"})
        try:
            e = hub.engine(); score, st = await learn_from_file(p, e["url"], e["model"])
        except Exception as e:
            log.exception("learn failed"); return JSONResponse({"ok": False, "error": str(e)}, 500)
        hub.score = score; hub.sampler.set_kit(score.kit)
        await hub.broadcast({"type": "score", "score": json.loads(score.to_json()), "gemma": st.notes_en,
                             "evidence": st.evidence, "confidence": st.confidence,
                             "summary_ml": structure_ml(score.thaalam, score.beats_per_cycle, len(score.notes), st.confidence)})
        return {"ok": True, "notes": len(score.notes), "thaalam": score.thaalam, "phrases": score.phrases, "confidence": st.confidence}

    @app.post("/api/compose")
    async def compose_ep(body: dict):
        brief, kit, thaalam = body.get("brief", "playful Onam melam"), body.get("kit", "chenda"), body.get("thaalam", "chempada 8")
        cycles, bpm = int(body.get("cycles", 4)), float(body.get("bpm", 90))
        composer, err = "Gemini (" + cfg.gemini_model + ")", None
        try:
            sc = compose(brief, kit, thaalam, cycles, bpm, cfg.gemini_model)
        except Exception as e:                                   # quota / offline -> compose on-device with Gemma
            err = str(e)[:160]; log.warning("Gemini compose failed (%s); falling back to Gemma", err)
            await hub.broadcast({"type": "status", "text": "Gemini unavailable — composing on-device with Gemma…"})
            try:
                e = hub.engine(); sc = await compose_gemma(hub.http, e["url"], e["model"], brief, kit, thaalam, cycles, bpm)
                composer = "Gemma on-device (" + cfg.gemma_model + ")"
            except Exception as e2:
                return JSONResponse({"ok": False, "error": f"gemini: {err} | gemma: {str(e2)[:160]}"}, 500)
        hub.score = sc; hub.sampler.set_kit(sc.kit)
        await hub.broadcast({"type": "score", "score": json.loads(sc.to_json()), "gemma": f"composed by {composer}"})
        return {"ok": True, "notes": len(sc.notes), "composer": composer, "gemini_error": err}

    @app.websocket("/ws")
    async def ws(sock: WebSocket):
        await sock.accept(); hub.clients.add(sock)
        await sock.send_text(json.dumps({"type": "status", "text": f"connected · mode {hub.mode}"}))
        try:
            while True:
                m = json.loads(await sock.receive_text()); t = m.get("type")
                if t == "key":
                    f = FINGER_KEYS.get(m.get("key", ""))
                    if f is not None: await hub.on_strike(Strike(f, time.monotonic() - INPUT_OFFSET_MS / 1000.0, float(m.get("v", 0.8)), "key"))
                elif t == "free":
                    hub.ladder = None
                    hub.bpm = float(m.get("bpm", hub.bpm)); hub.cycle = int(m.get("cycle", hub.cycle)); hub.click_mode = m.get("click", hub.click_mode)
                    await hub.start_free()
                elif t == "kit": hub.sampler.set_kit(m.get("kit", "chenda")); await hub.broadcast({"type": "kit", "kit": hub.sampler.kit})
                elif t == "practice": hub.ladder = None; await hub.start_practice(m.get("phrase"), float(m.get("speed", 1.0)))
                elif t == "listen": hub.ladder = None; await hub.start_listen(m.get("phrase"), float(m.get("speed", 1.0)))
                elif t == "karaoke":                      # vaaythari chant toggle; _chant() reads this flag
                    hub.karaoke = bool(m.get("on", False))
                    if not hub.karaoke: speech.stop()
                    await hub.broadcast({"type": "status", "text": f"vaaythari chant {'on' if hub.karaoke else 'off'}"})
                elif t == "ladder":                       # kaalam ladder: same phrase through a tempo sequence, auto-advancing
                    try:
                        scales = tuple(float(x) for x in m["scales"]) if m.get("scales") else DEFAULT_SCALES
                        await hub.start_ladder(m.get("phrase"), scales)
                    except (ValueError, TypeError) as e:
                        await hub.broadcast({"type": "status", "text": f"ladder error: {e}"})
                elif t == "stop": hub.ladder = None; await hub.stop_all(); hub.mode = "idle"
                elif t == "load_score": hub.score = score_from_dict(m.get("score", {}))
                elif t == "game":                        # Repeat after Maveli: next round (level up on pass, same level on fail)
                    passed = bool(m.get("passed", True))
                    if hub.game_history: hub.game_history[-1]["result"] = "pass" if passed else "fail"
                    hub.game_level = hub.game_level + 1 if passed else max(1, hub.game_level)
                    if m.get("reset"): hub.game_level, hub.game_history = 1, []
                    e = hub.engine(); r = await next_round(hub.http, e["url"], e["model"], hub.game_level, hub.game_history)
                    hub.game_history.append({"level": r.level, "phrase": list(r.phrase), "bpm": r.bpm})
                    hub.score = phrase_to_score(list(r.phrase), r.bpm, title=f"Maveli L{r.level}", cycles=1)
                    await hub.broadcast({"type": "game", "level": r.level, "phrase": list(r.phrase), "bpm": r.bpm, "banter": r.banter, "source": r.source})
                    await hub.broadcast({"type": "score", "score": json.loads(hub.score.to_json()), "gemma": r.banter})
                elif t == "phrase":                      # vaaythari phrase -> practice score (uses asan.config.SYLLABLE_FINGER)
                    try:
                        hub.score = phrase_to_score([x for x in str(m.get("text", "")).replace("-", " ").split() if x], float(m.get("bpm", hub.bpm)), cycles=int(m.get("cycles", 2)))
                        await hub.broadcast({"type": "score", "score": json.loads(hub.score.to_json()), "gemma": "vaaythari phrase"})
                    except ValueError as e:
                        await hub.broadcast({"type": "status", "text": f"phrase error: {e}"})
        except WebSocketDisconnect:
            hub.clients.discard(sock)
            if not hub.clients and hub.mode in ("listen", "practice"):   # last dashboard gone (reload/close): stop playback + ladder + chant
                hub.ladder = None; await hub.stop_all(); hub.mode = "idle"
    return app


def main() -> None:
    import argparse, uvicorn
    ap = argparse.ArgumentParser(); ap.add_argument("--dry", action="store_true"); ap.add_argument("--port", type=int, default=8000)
    ap.add_argument("--model", default=None); a = ap.parse_args()
    logging.basicConfig(level=logging.INFO)
    cfg = Config(dry=a.dry, port=a.port, **({"gemma_model": a.model} if a.model else {}))
    uvicorn.run(create_app(cfg), host=cfg.host, port=cfg.port)


if __name__ == "__main__":
    main()
