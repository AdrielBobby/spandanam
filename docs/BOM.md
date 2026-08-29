# Bill of Materials — Melam Asan

Target: **3 drummer nodes + 1 hub**. Everything marked ✅ is in the TinkerSpace shared inventory (XIAO, Grove, sensors, motors); ⚠️ is bring‑your‑own or buy locally (Kalamassery/Ernakulam electronics shops, or Robu/Amazon if pre‑ordered).

## Per node (×3, ideally ×4 incl. asan)
| Qty | Part | Role | Source | ≈₹ |
|---|---|---|---|---|
| 1 | Seeed **XIAO ESP32‑S3** (Sense variant OK) | MCU + Wi‑Fi | ✅ | 900 |
| 1 | **MPU6050** (or Grove IMU 6/9‑DoF) | Stick/wrist IMU — strike detection, ±16 g | ✅ | 150 |
| 1 | **MAX30102** PPG (heart rate) | Wrist HR for fatigue | ⚠️ | 250 |
| 1 | **Coin vibration motor** 3 V (10 mm) | Haptic cue | ⚠️ (or from inventory motors) | 60 |
| 1 | 2N2222 / S8050 NPN + 1 kΩ + 1N4148 diode | Motor driver | ✅ lab | 15 |
| 1 | 3.7 V LiPo 400–1000 mAh + JST | Power | ⚠️ | 250 |
| 1 | Slide switch | Power | ✅ | 10 |
| 1 | Velcro wrist strap + zip ties | Mounting | ⚠️ | 50 |
| – | Dupont wires, heat‑shrink, hot glue | | ✅ | – |
| 1 | Laser‑cut/3D‑printed wrist puck + stick clip | Enclosure | ✅ TinkerSpace | – |

**Node subtotal ≈ ₹1,700 · ×3 ≈ ₹5,100**

## Hub (×1)
| Part | Role | Note |
|---|---|---|
| Laptop (Apple Silicon / any with ≥8 GB) **or** Raspberry Pi 5 (8 GB) | Runs Ollama + **Gemma 3n E4B** (or `gemma3:4b`) fully offline | Pi 5 gives the "true edge" story; laptop is the safe fallback |
| Phone hotspot or laptop hotspot / travel router | Wi‑Fi for nodes | Name it `melam-hub`, no internet needed |
| USB mic (any) | 2 s ensemble audio clips for Gemma 3n | Optional but the standout feature |
| USB‑C cable, powered USB hub | Flashing / power | |

## Demo props
| Part | Note |
|---|---|
| Chenda (borrow) **or** 2–3 drums / cardboard boxes | Anything struck with a stick works |
| Drum sticks ×3 (chenda kol or wooden dowels) | IMU clips onto these |
| Blindfold — no. Onam props: kasavu cloth for the console table | Presentation |

## Buy‑now list (things TinkerSpace probably won't have)
- 3× MAX30102 modules
- 3× coin vibration motors
- 3× LiPo 3.7 V + JST connectors
- Velcro straps
- USB mic (if none in laptop)

## Software
- Ollama ≥0.6 with `ollama pull gemma3n:e4b` (≈7.5 GB) — pull **now**, before venue Wi‑Fi dies
- Fallback: `ollama pull gemma3:4b`
- Arduino IDE 2 + ESP32 board package + libs in `firmware/melam_node/README.md`
- Python 3.10+, `pip install -e hub[dev]`
- `GEMINI_API_KEY` from Google AI Studio (post‑session report only)
