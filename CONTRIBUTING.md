# Contributing

Hackathon mode: small commits, push often, `main` is always demo‑able. Project: Viralthaalam (air-percussion glove, Gemma finger thaalam).

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
