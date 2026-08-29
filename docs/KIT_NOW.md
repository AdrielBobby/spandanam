# Building with what we have right now (Pi 5 · 1 IMU · 3 buzzers)

## Wiring (Pi 5 header)
| Part | Pi pin | Note |
|---|---|---|
| Buzzer 1 — **chest** (bass chenda) | GPIO18 (pin 12) + GND | 100 Ω in series; NPN transistor if buzzer >40 mA |
| Buzzer 2 — **wrist** (treble chenda) | GPIO13 (pin 33) + GND | |
| Buzzer 3 — **fingertip** (cymbals/horns) | GPIO12 (pin 32) + GND | |
| IMU (MPU6050) — tap wrist | SDA GPIO2 (pin 3), SCL GPIO3 (pin 5), 3V3, GND | `sudo raspi-config` → enable I2C |
| USB mic | any USB | or `arecord -l` to find it |

Tape/velcro buzzers flat against skin (sternum, inner wrist, index fingertip). Active buzzers > piezo for feel.

## Run on the Pi
```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama pull gemma3n:e2b          # e4b if RAM allows; e2b is faster on Pi 5
cd hub && pip install -e ".[dev]" soundfile smbus2
python -m spandanam.main --band gpio --wav ../assets/panchari.wav   # dev from recording
python -m spandanam.main --band gpio                                 # live mic
```

## Upgrade path when parts arrive
- 8 coin motors → keep `--band gpio`, add pins to `pi_band.ZONE_PINS`, or move to the XIAO band (`firmware/`).
- Second IMU → tap‑along for a second wearer.
