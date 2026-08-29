# Thaalam 🖐️🥁

**Air percussion on your fingers, with Yousician‑style real‑time feedback — and Gemma 3n on a Raspberry Pi 5 turning any track into a finger‑by‑finger thaalam lesson.**

*Thaalam* — rhythm. Built in 24 h at the [Google Physical AI Hackathon: Onam Edition](https://physicalai.tinkerhub.org/), TinkerSpace Kochi, 29–30 Aug 2026 · Themes: **Onakalikal · Homecoming** · Powered by Gemma 3n + Gemini.

## What it is
A glove with an IMU, a vibration motor and an LED on each of five fingers. Strike the air → the Pi plays that finger's drum voice from the speaker. The fingers **feel the tempo** (buzz), **see which finger is next** (LED), and the dashboard shows falling notes per finger with PERFECT / GOOD / LATE / WRONG FINGER judged live.

| Mode | What happens |
|---|---|
| **Free flow** | Pick an instrument (chenda, mridangam, tabla, kit). Tempo pulses on your fingers (walk thumb→pinky / all / downbeat). Play whatever you feel. |
| **Learn** | Upload an mp3/wav. Onsets + timbres are extracted, then **Gemma structures it**: names the thaalam and cycle length, assigns each timbre to a finger with a voice name and vaaythari syllable, cuts it into practice phrases. Or ask **Gemini to compose** a new piece from a one‑line brief. |
| **Practice** | Notes fall down five lanes; LEDs + buzz cue the finger ~120 ms ahead; every hit is judged in real time; stars + score at the end; **Gemma coaches** you in Malayalam + English and picks your next drill. |

## Sense → Think → Act
- **Sense:** MPU6050 per finger (today: 1 real IMU on the thumb, 4 fingers emulated by laptop keys `J K L ;` — same `Strike` event, swap in gloves later with zero code change).
- **Think:** timing math judges hits (<1 ms, deterministic). **Gemma 3n on‑device** does what math can't: hears the track and decides its musical structure, how it maps onto five fingers, what to practise, and how to coach. **Gemini** composes new pieces.
- **Act:** speaker (synth kits, no samples needed), 5 buzzers, 5 LEDs, live dashboard.

**Removal tests.** Take the glove away → nothing to strike, cue, or judge. Take Gemma away → onsets with no thaalam, no finger map, no lesson, no coach.

## Repo
```
hub/viral/
  server.py         FastAPI + WebSocket hub: modes, inputs, cues, judging, coaching
  static/index.html dashboard: falling-note lanes, pads, free-flow controls, learn/compose, practice
  judge.py          real-time PERFECT/GOOD/LATE/WRONG/MISS + streak/points (pure functions)
  score.py          finger Score model (notes, finger_map, phrases) — JSON in/out
  transcribe.py     librosa onsets + timbre clustering → events (deterministic)
  gemma_thaalam.py  Gemma 3n: structure() and coach()  — strict JSON, offline
  gemini_compose.py Gemini: brief → symbolic score
  learn.py          file → transcription → Gemma → Score
  metronome.py      tempo on fingers (walk/all/downbeat)
  sound.py          synth percussion kits (chenda/mridangam/tabla/kit); WAV samples optional
  hardware.py       5 buzzers + 5 LEDs on Pi GPIO (--dry on laptop)
  imu.py            MPU6050 → strikes (peak g, tilt)
  bridge.py         asan ↔ viral: vaaythari phrase → Score; deterministic analysis → Gemma coach input
hub/asan/           pure scheduler / scorer / practice / analysis layer + console CLIs (Adriel) — 80 tests
  scheduler.py      phrase → expected finger events; score_events() with timing windows
  practice.py       summaries, cues, result tables
  analysis.py       deterministic post-round facts (weak fingers, dominant error, next tempo/phrase) that Gemma explains
  input_sources.py  InputEvent + keyboard simulator (Windows console)
tests/              pytest — 91 tests across both packages
docs/               CREATIVE_ELEMENTS · GEMMA_MAX · SHOPPING · PLAN_24H · WIRING
```

## Quick start
```bash
# Pi 5 (or a laptop with --dry)
curl -fsSL https://ollama.com/install.sh | sh && ollama pull gemma3n:e4b     # e2b if slow
sudo apt install -y libportaudio2 libsndfile1 i2c-tools && sudo raspi-config nonint do_i2c 0
cd hub && pip install -e ".[dev]"
python -m viral.server --dry        # laptop
python -m viral.server              # Pi: GPIO + IMU
# open http://<pi-ip>:8000  — SPACE = thumb (or real IMU), J K L ; = index..pinky
export GEMINI_API_KEY=...           # only for Compose
```
Wiring: [`docs/WIRING.md`](docs/WIRING.md) · Parts: [`docs/SHOPPING.md`](docs/SHOPPING.md) · Ideas: [`docs/CREATIVE_ELEMENTS.md`](docs/CREATIVE_ELEMENTS.md)

## Tests
```bash
cd hub && pytest
```

## Team
- Ryyan Safar — [@ryyansafar](https://github.com/ryyansafar) — AI/ML
- Adriel Bobby — [@AdrielBobby](https://github.com/AdrielBobby) — backend
- Fathima Moonam Kandathil — [@fathima-004](https://github.com/fathima-004) — hardware
- Paulyn — UI

## Socials & Support
- Portfolio: https://ryyansafar.site
- GitHub: https://github.com/ryyansafar
- Buy Me a Coffee: https://buymeacoffee.com/ryyansafar
- PayPal: https://www.paypal.com/paypalme/ryyansafar
- Razorpay: https://razorpay.me/@ryyansafar

## License
MIT — see [LICENSE](LICENSE).
