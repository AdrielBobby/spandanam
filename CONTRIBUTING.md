# Contributing

Hackathon mode: small commits, push often, `main` is always demo‑able. Project: Thaalam (air-percussion glove, Gemma finger thaalam).

## Ownership (hackathon, 29–30 Aug)
| Lane | Owner | Files you own — others only touch via a quick ping |
|---|---|---|
| **Hardware** | Fathima | `hub/viral/hardware.py`, `hub/viral/imu.py`, `docs/WIRING.md`, `docs/SHOPPING.md`, glove build |
| **UI** | Paulyn | `hub/viral/static/index.html` (+ any new static assets) — talks to the server only through the WebSocket contract below |
| **Backend** | Adriel | `hub/viral/server.py`, `judge.py`, `score.py`, `metronome.py`, `sound.py`, `hub/asan/*`, tests for those |
| **AI/ML** | Ryyan | `hub/viral/gemma_thaalam.py`, `gemini_compose.py`, `transcribe.py`, `learn.py`, `bridge.py`, `gemma_cli.py`, `docs/GEMMA_MAX.md` |
| Shared | all | README, docs/PLAN_24H.md, CONTRIBUTING (this contract) |

**WebSocket contract** (server → dashboard): `strike{finger,v,src,judge?,offset_ms?,note?,streak?,points?}` · `click{beat,finger,down}` · `score{score,gemma}` · `practice_start{score,lead_in_s}` · `miss{notes,streak}` · `practice_end{summary}` · `coach{say_en,say_ml,drill_phrase,drill_bpm,focus}` · `status{text}` · `kit{kit}` · `game{level,phrase,bpm,banter,source}` (followed by a `score` message — call `practice` to play it).
Dashboard → server: `key{key,v}` · `free{bpm,cycle,click}` · `kit{kit}` · `practice{phrase,speed}` · `stop` · `phrase{text,bpm,cycles}` · `load_score{score}` · `game{passed?,reset?}` (Repeat after Maveli: `reset:true` starts at level 1; send `passed` from the last `practice_end` — stars ≥ 2 = pass).
Add a message type? Add it here in the same commit.

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
