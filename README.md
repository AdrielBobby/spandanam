# Vaaythari 🥁🗣️

**An offline Gemma chenda asan.** It chants a vaaythari phrase, taps it on your wrist, listens to you play it back, tells you — in Malayalam — what you got wrong and *why*, and composes your next drill. On a Raspberry Pi 5. No internet.

Built in 24 h at the [Google Physical AI Hackathon: Onam Edition](https://physicalai.tinkerhub.org/), TinkerSpace Kochi, 29–30 Aug 2026 · Themes: **Onakalikal · Homecoming** · Powered by Gemma 3n + Gemini.

## Why
Chenda has been taught for centuries by *vaaythari* — the asan chants syllables (*tha‑ki‑ta, dhim‑tha‑ka*), the student plays them back, the asan corrects. Good asans are few, far, and expensive; most kids who want to play for Onam never get one. Vaaythari puts that loop in a box.

## Sense → Think → Act
| | |
|---|---|
| **Sense** | Mic hears the student's strokes. MPU6050 on the stick measures every hit's force and wrist angle. Mic also hears the student *talk* to the asan. |
| **Think (Gemma 3n, on‑device)** | Hears the clip and **transcribes the playing into syllables** ("you played tha‑ka‑*ta‑ta*"), compares with what it asked, **fuses the IMU** ("third stroke weak because your wrist dropped"), **composes the next drill** under teaching rules, and **understands Malayalam requests** ("asan, pathukke"). Strict JSON out. |
| **Act** | Three wrist buzzers tap the phrase before you play — right hand, left hand, accent — so you *feel* it first. The asan speaks Malayalam (espeak‑ng). Weak strokes get a haptic nudge. |

**Gemini API** (cloud, after class): the asan's notebook — progress report and tomorrow's lesson plan.

**Removal tests.** No mic/IMU/buzzers → nothing to hear, measure, or teach with. No Gemma → a metronome that can't tell *tha* from *ka*. Timing is math and we say so; Gemma does only what a model can do — see [`docs/GEMMA_MAX.md`](docs/GEMMA_MAX.md).

## Creative modes
Call‑and‑response · Composer asan · Talk to the asan · Feel‑first (deaf learners) · Kaalam ladder · Melam mode (2 students) · Onam mini‑game · Stick posture coach · Visible vaaythari diff — scoped in [`docs/CREATIVE_ELEMENTS.md`](docs/CREATIVE_ELEMENTS.md).

## Repo
```
hub/asan/
  main.py          lesson loop: demonstrate → listen → hear → correct → teach
  gemma_asan.py    Gemma 3n: hear() teach() intent()  — strict JSON, offline
  vaaythari.py     syllables ↔ hands, tap schedule, asked-vs-played diff
  imu.py           MPU6050 stick reader → strokes (peak g, tilt)
  pi_band.py       3 wrist buzzers on Pi 5 PWM (--dry for laptop)
  speech.py        espeak-ng / say  (Malayalam TTS); STT is Gemma itself
  audio.py         mic → 16 kHz WAV
  gemini_notebook.py  post-class report (Gemini API)
tests/             pytest
docs/              CREATIVE_ELEMENTS · GEMMA_MAX · SHOPPING · PLAN_24H
```

## Quick start
```bash
# Pi 5 (or laptop with --dry)
curl -fsSL https://ollama.com/install.sh | sh && ollama pull gemma3n:e4b   # e2b if slow
sudo apt install -y espeak-ng portaudio19-dev i2c-tools && sudo raspi-config nonint do_i2c 0
cd hub && pip install -e ".[dev]" smbus2

python -m asan.main --dry --lang en          # laptop: no GPIO/I2C
python -m asan.main --voice                  # Pi: buzzers + IMU + talk to the asan
GEMINI_API_KEY=... python -c "from asan.gemini_notebook import report; from pathlib import Path; print(report(Path('data/sessions/<id>/session.json'), 'gemini-2.5-flash'))"
```
Wiring: buzzers → GPIO18 (right) / GPIO13 (left) / GPIO12 (accent) via 100 Ω to GND; MPU6050 → SDA GPIO2, SCL GPIO3, 3V3, GND. Shopping list: [`docs/SHOPPING.md`](docs/SHOPPING.md).

## Tests
```bash
cd hub && pytest
```

## Team
- Ryyan Safar — [@ryyansafar](https://github.com/ryyansafar)
- Adriel Bobby — [@AdrielBobby](https://github.com/AdrielBobby)
- Fathima Moonam Kandathil — [@fathima-004](https://github.com/fathima-004)

## Socials & Support
- Portfolio: https://ryyansafar.site
- GitHub: https://github.com/ryyansafar
- Buy Me a Coffee: https://buymeacoffee.com/ryyansafar
- PayPal: https://www.paypal.com/paypalme/ryyansafar
- Razorpay: https://razorpay.me/@ryyansafar

## License
MIT — see [LICENSE](LICENSE).
