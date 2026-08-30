# Contributing

Hackathon mode: small commits, push often, `main` is always demo‑able. Project: Thaalam (air-percussion glove, Gemma finger thaalam).

## Ownership (hackathon, 29–30 Aug)
| Lane | Owner | Files you own — others only touch via a quick ping |
|---|---|---|
| **Hardware** | Fathima | `hub/viral/hardware.py`, `hub/viral/imu.py`, `docs/WIRING.md`, `docs/SHOPPING.md`, glove build |
| **UI** | Adriel | `hub/viral/static/index.html`, `style.css`, `app.js` (+ any new static/asset files) — talks to the server only through the WebSocket contract below |
| **Backend** | Adriel | `hub/viral/server.py`, `judge.py`, `score.py`, `metronome.py`, `sound.py`, `ladder.py`, `motion.py`, `hub/asan/*`, `dashboard/`, `content/lessons/`, tests for those |
| **AI/ML** | Ryyan | `hub/viral/gemma_thaalam.py`, `gemini_compose.py`, `transcribe.py`, `learn.py`, `bridge.py`, `gemma_cli.py`, `docs/GEMMA_MAX.md` |
| Shared | all | README, docs/PLAN_24H.md, CONTRIBUTING (this contract) |

**WebSocket contract** (server → dashboard): `strike{finger,v,src,judge?,offset_ms?,note?,streak?,points?}` · `click{beat,finger,down}` · `score{score,gemma,evidence,confidence,summary_ml}` · `/api/state.labels_ml` = Malayalam UI labels · `/api/state.audio_device` + `POST /api/audio/reopen` (rebind to current default output; plays a confirmation hit) · `GET /api/gemma` = all Gemma engines (model/endpoint/loaded/on_device) + active `mode`; `POST /api/gemma/select {mode: <engine>|both}`; engines come from `GEMMA_ENGINES="laptop=http://127.0.0.1:11435|gemma3n:e4b,pi=http://127.0.0.1:11434|gemma3:1b"`. In `both` mode the `coach` message carries `results:[{engine,model,on_device,seconds,say_en,say_ml,...}]` for side-by-side display (ആശാൻ പറയുന്നു etc.) · `practice_start{score,lead_in_s}` · `miss{notes,streak}` · `practice_end{summary}` · `coach{say_en,say_ml (Malayalam script, deterministic),say_manglish (Gemma),drill_phrase,drill_bpm,focus}` · `status{text}` · `kit{kit}` · `game{level,phrase,bpm,banter,source}` (followed by a `score` message — call `practice` to play it) · `ladder_start{total_steps,bpm_scale}` · `ladder_step_up{total_steps,step,bpm_scale}` · `ladder_retry{total_steps,step,bpm_scale}` · `ladder_complete{total_steps,step:null,bpm_scale:null}` (kaalam ladder: each `practice_end` auto-advances or retries — see `ladder.py`).
Dashboard → server: `key{key,v}` · `free{bpm,cycle,click}` · `kit{kit}` · `practice{phrase,speed}` · `listen{phrase,speed}` (auto-plays the score through speaker + LEDs, `practice_start` carries `listen:true`, strikes carry `judge:"auto"`) · `stop` · `phrase{text,bpm,cycles}` · `load_score{score}` · `game{passed?,reset?}` (Repeat after Maveli: `reset:true` starts at level 1; send `passed` from the last `practice_end` — stars ≥ 2 = pass) · `ladder{phrase?,scales?}` (kaalam ladder: default scales `[0.6,0.8,1.0,2.0]`; sending `practice`/`listen`/`free`/`stop` cancels any ladder in progress).
Add a message type? Add it here in the same commit.

**Motion coach (IMU tilt).** `practice_end.summary` gains an optional `motion` field — `{avg_tilt_deg, avg_peak_g, verdict:"good"|"flat", hint}` — aggregated over that round's `imu.Stroke`s (see `motion.py`). Only ever present for rounds with real thumb strikes: the only finger with a physical IMU today (`imu_strike_g` gates which accelerometer jumps register as a `Stroke` at all, and `--dry` mode's `MPU6050Reader` never yields any). Absent from `summary` entirely when there were none, rather than a null/empty object. `FLAT_TILT_DEG=30.0` is an untuned starting guess — needs real hardware to calibrate.

**Vaaythari karaoke (TTS chant).** When Practice or Listen starts (including each round of a kaalam ladder — it calls `start_practice` internally), the server chants the score's vaaythari syllables aloud via `speech.chant()` (espeak-ng / macOS `say`), timed to the score's bpm. Runs in a thread executor during the round's lead-in, off the event loop, since it's a blocking subprocess call. No new WS message — it's server-side audio only. Silently skipped for scores with no `Note.label` (e.g. some learn/compose results), and silently logs instead of speaking if neither TTS backend is installed — see `speech.py`.

**Kaalam ladder example session** (falling notes/judging/coaching already play through unchanged via the existing `practice_start`/`strike`/`practice_end`/`coach` handling; the step/scale narration below is the only new UI surface):
```jsonc
// client, once a phrase/score is loaded:
{"type": "ladder", "scales": [0.6, 0.8, 1.0, 2.0]}   // scales optional, this is the default

// server, conceptually:
// ladder_start{total_steps:4, bpm_scale:0.6} -> practice_start (round 1 plays)
// practice_end -> coach -> ladder_step_up{step:1, bpm_scale:0.8} -> practice_start (round 2 plays)
// ... or, on a failed round instead: ladder_retry{step:0, bpm_scale:0.6} -> practice_start (same step replays)
// ... until: ladder_complete{step:null, bpm_scale:null} after the last step passes
```

## Branches
- `main` — always runs. Merge via PR or fast‑forward after a quick check.
- `fw/*` firmware, `hub/*` hub, `docs/*` docs.

## Commit format
`<type>: <description>` — types: feat, fix, refactor, docs, test, chore.

## Before pushing
```bash
cd hub && pytest -q
```
Firmware changes: build for XIAO_ESP32S3 and confirm buzzers+LEDs cue and the IMU triggers a sound on the Pi.

## Style
- Python: pure functions, frozen dataclasses, no in‑place mutation of shared state, files < 300 lines.
- Hardware: `--dry` must always work on a laptop with no GPIO/I2C.
- Never commit `config.h`, `.env`, or session data.

## Socials & Support
- Portfolio: https://ryyansafar.site
- GitHub: https://github.com/ryyansafar
- Buy Me a Coffee: https://buymeacoffee.com/ryyansafar
- PayPal: https://www.paypal.com/paypalme/ryyansafar
- Razorpay: https://razorpay.me/@ryyansafar
