# Thaalam 🖐️🥁

**Air percussion on your fingers with real‑time feedback — and Gemma running locally that turns any track into a finger‑by‑finger *thaalam* lesson and coaches you back like an Ashaan.**

🏆 **Winner, Best Use of Gemma** at the [Google Physical AI Hackathon: Onam Edition](https://physicalai.tinkerhub.org/), TinkerSpace Kochi, 29–30 Aug 2026. Built in 24 hours · Themes: **Onakalikal · Homecoming** · Powered by **Gemma** (on‑device) + **Gemini** (cloud).

## What it is
A glove with an IMU, a vibration motor and an LED per finger. Strike the air → the drum voice for that finger plays. The fingers **feel the tempo** (buzz) and **see which finger is next** (LED); the dashboard shows falling notes per finger, judged live — PERFECT · കൃത്യം / GOOD / LATE / WRONG FINGER / MISS — with a 3D chenda stage.

| Mode | What happens |
|---|---|
| **Free flow** | Pick an instrument (chenda from real strikes, mridangam, tabla, kit — modal synthesis). Tempo pulses on your fingers. Play. |
| **Learn** | Upload any mp3/wav. Onsets + timbres are extracted and **Gemma structures it**: thaalam & cycle (with evidence + confidence), finger map with vaaythari syllables, practice phrases. Or **compose** a new piece (Gemini; on‑device Gemma fallback). |
| **Practice** | Yousician‑style lanes, LED/buzz cue ~120 ms ahead, live judging, stars. **Ashaan says** — coaching in Malayalam (deterministic, accurate), English and Manglish (Gemma). Kaalam ladder auto‑advances tempo; optional vaaythari karaoke chant; IMU motion coach. |
| **Repeat after Maveli** | Gemma generates ever‑harder phrases; longest streak wins. |

## Sense → Think → Act
- **Sense** — MPU6050 on the finger (peak‑vs‑rest strike detection, 120 ms refractory); laptop keys `SPACE J K L ;` emulate the other fingers with the identical `Strike` event. Mic for live audio.
- **Think** — timing math judges every hit (<1 ms, deterministic; we say so). **Gemma** does what math cannot: hears a track and decides its musical structure and finger mapping, coaches from the deterministic analysis, composes drills and game phrases. **Gemini** composes new pieces.
- **Act** — 5 buzzers + 5 LEDs on Pi GPIO, browser + Pi audio, live dashboard.

**Removal tests.** No glove → nothing to strike, cue or judge. No Gemma → onsets with no thaalam, no finger map, no lesson, no coach.

## Gemma, exactly
| Engine | Model | Where | Use |
|---|---|---|---|
| `laptop` | **gemma3n:e4b** (Gemma 3n, multimodal) via Ollama | laptop GPU, reached from the Pi over an SSH tunnel | default: structure, coach, game, compose‑fallback |
| `pi` | **gemma2:2b** via Ollama | **on the Raspberry Pi 5 itself** (4 GB) | fully on‑device mode |
| both | — | — | side‑by‑side answers with timings on the dashboard |

`GET /api/gemma` shows which engines are loaded and active; the dashboard's **Gemma engine** card switches between them. `gemma3n:e2b` does not fit in 4 GB (OOM‑killed) — documented in `docs/GEMMA_MAX.md`.

## Repo
```
hub/viral/      server.py (FastAPI + WebSocket) · static/ (dashboard: app.js, style.css, index.html)
                judge.py · score.py · transcribe.py · learn.py · gemma_thaalam.py · gemma_game.py · gemma_compose.py
                gemini_compose.py · malayalam.py · bridge.py · sound.py · sample_kit.py · build_chenda_kit.py
                hardware.py · imu.py · motion.py · ladder.py · metronome.py · speech.py
hub/asan/       deterministic scheduler / practice / analysis layer + lessons (content/lessons/*.json)
tests/          182 tests (pytest)
docs/           GEMMA_MAX · WIRING · SHOPPING · CREATIVE_ELEMENTS · PLAN_24H
scripts/        thaalam.service · pi_run.sh · mac_gemma_tunnel.sh
```

## Run
```bash
# Raspberry Pi 5 (Pi OS Lite)
curl -fsSL https://ollama.com/install.sh | sh && ollama pull gemma2:2b
sudo apt install -y libportaudio2 libsndfile1 ffmpeg && sudo raspi-config nonint do_i2c 0
cd hub && python3 -m venv .venv && . .venv/bin/activate && pip install -e ".[dev]"
sudo cp ../scripts/thaalam.service /etc/systemd/system/ && sudo systemctl enable --now thaalam
# open http://<pi-ip>:8000  (Safari/Chrome; on macOS allow Chrome → Privacy → Local Network)

# laptop with a bigger Gemma (optional): ollama pull gemma3n:e4b, then keep the tunnel up
./scripts/mac_gemma_tunnel.sh ryyan@<pi-ip>
# service env (drop-in): GEMMA_ENGINES="laptop=http://127.0.0.1:11435|gemma3n:e4b,pi=http://127.0.0.1:11434|gemma2:2b"
# knobs: INPUT_OFFSET_MS (input latency), IMU_STRIKE_G (strike threshold), THAALAM_ARGS=--dry (no GPIO), REAL_KITS=1
```
Wiring: [`docs/WIRING.md`](docs/WIRING.md) · Parts: [`docs/SHOPPING.md`](docs/SHOPPING.md) · Gemma notes: [`docs/GEMMA_MAX.md`](docs/GEMMA_MAX.md)

## Tests
```bash
cd hub && pytest
```

## Honest limits
Cycle detection is confident on clean/close‑mic recordings and correctly *uncertain* (labelled, confidence ≤0.5) on 60 s festival crowd audio. The 2B on‑device model coaches more plainly than the 4B. No Malayalam TTS exists offline — the chant uses an Indic voice; Malayalam text is generated deterministically and is accurate.

## Team
- Ryyan Safar — [@ryyansafar](https://github.com/ryyansafar) — AI/ML
- Adriel Bobby — [@AdrielBobby](https://github.com/AdrielBobby) — backend & UI
- Fathima Moonam Kandathil — [@fathima-004](https://github.com/fathima-004) — hardware

## Socials & Support
- Portfolio: https://ryyansafar.site
- GitHub: https://github.com/ryyansafar
- Buy Me a Coffee: https://buymeacoffee.com/ryyansafar
- PayPal: https://www.paypal.com/paypalme/ryyansafar
- Razorpay: https://razorpay.me/@ryyansafar

## License
MIT — see [LICENSE](LICENSE).
