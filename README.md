# Melam Asan 🥁

**An on‑device Gemma "lead drummer" for chenda melam — keeps a troupe in sync, tracks the kaalam, and buzzes a tiring drummer to rest before they collapse.**

Built in 24 h at the [Google Physical AI Hackathon: Onam Edition](https://physicalai.tinkerhub.org/), TinkerSpace Kochi, 29–30 Aug 2026 · Theme: **Onakalikal / Homecoming (care)** · Powered by Gemma + Gemini.

## The problem
Chenda melam ensembles (Panchari, Pandi) play for hours in Kerala heat during Onam and temple festivals. Beginners drift out of sync with the *asan* (lead), kaalam (tempo‑stage) transitions are missed, and heat exhaustion among drummers is common but unmonitored.

## What it does — Sense → Think → Act
| | |
|---|---|
| **Sense** | Each drummer wears a wrist puck: XIAO ESP32‑S3 + IMU on the stick + heart‑rate sensor. 100 Hz telemetry over local Wi‑Fi. A mic on the hub hears the ensemble. |
| **Think** | DSP finds every strike, tempo and phase error. **Gemma 3n runs fully offline on the hub** and does what DSP can't: recognises which *kaalam* the troupe is in, who broke the pattern, and grades each drummer's fatigue (HR slope × amplitude decay × timing jitter) with a one‑line reason for the asan. |
| **Act** | Vibration motor on the wrist: 1 pulse = speed up, 2 = slow down, 3 = kaalam change, long buzz = *rest now*. Live asan console on screen. |

After the session, the **Gemini API** turns the telemetry + video into a coaching report per drummer.

**Hardware removal test:** unplug the IMUs and the system has nothing to hear, reason about, or command. ✔

## Why Gemma on‑device (not just an API call)
- Works at a temple ground with **zero connectivity**.
- Drummer **biometrics never leave the device**.
- Gemma 3n's native **audio input** lets it judge the musical state from sound + sensors together — a job neither a threshold nor a cloud round‑trip can do at 2 s cadence.

## Repo layout
```
firmware/melam_node/   XIAO ESP32-S3 node (IMU + PPG + vibra motor, UDP)
hub/melam/             Python hub: ingest, strike, sync, fatigue, gemma_coach, haptics, console, gemini_report
hub/melam/simulate.py  fake drummers for dev without hardware
tests/                 unit tests (pytest)
docs/                  BOM, ARCHITECTURE, PLAN_24H
```

## Quick start
```bash
# hub (laptop or Raspberry Pi 5)
brew install ollama   # or: curl -fsSL https://ollama.com/install.sh | sh
ollama pull gemma3n:e4b            # fallback: gemma3:4b
cd hub && pip install -e ".[dev]" && cd ..
python -m melam.main --audio       # add -v for debug; run from hub/

# no hardware yet? in another shell:
python -m melam.simulate --bpm 80

# post-session report (needs GEMINI_API_KEY from Google AI Studio)
python -c "from melam.gemini_report import *; from pathlib import Path; \
  print(generate_report(Path('data/sessions/<id>/session.json'), None, 'gemini-2.5-flash'))"
```
Firmware: see [`firmware/melam_node/README.md`](firmware/melam_node/README.md). Components: [`docs/BOM.md`](docs/BOM.md).

## Tests
```bash
cd hub && pytest --cov=melam
```

## Team
- Ryyan Safar — [@ryyansafar](https://github.com/ryyansafar)
- Adriel Bobby — [@AdrielBobby](https://github.com/AdrielBobby)
- Fathima — [@fathima-004](https://github.com/fathima-004)

## Socials & Support
- Portfolio: https://ryyansafar.site
- GitHub: https://github.com/ryyansafar
- Buy Me a Coffee: https://buymeacoffee.com/ryyansafar
- PayPal: https://www.paypal.com/paypalme/ryyansafar
- Razorpay: https://razorpay.me/@ryyansafar

## License
MIT — see [LICENSE](LICENSE).
