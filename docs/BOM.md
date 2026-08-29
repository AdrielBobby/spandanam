# Bill of Materials — Spandanam

One wearable (band + 2 wrist cuffs) + one hub. ✅ = TinkerSpace shared inventory · ⚠️ = buy/bring.

## Wearable
| Qty | Part | Role | Src | ≈₹ |
|---|---|---|---|---|
| 1 | Seeed **XIAO ESP32‑S3** | drives 8 PWM motor channels over Wi‑Fi | ✅ | 900 |
| 8 | **Coin vibration motors** 10 mm 3 V (LRA if available — crisper) | chest, back, 2 wrists, 2 shoulders, 2 fingertips | ⚠️ (inventory motors as fallback) | 8×60 |
| 1–2 | **ULN2003** Darlington array (7 ch) + 1 NPN, **or** 2× TB6612FNG / L293D | motor driver, PWM intensity | ✅ lab | 80 |
| 8 | 1N4148 flyback diodes, 8× 100 nF caps | motor noise | ✅ | 30 |
| 1 | 3.7 V LiPo 1000–2000 mAh + JST + slide switch | power (8 motors ≈ 0.6 A peak) | ⚠️ | 350 |
| 1 | TP4056 charger board | recharge | ⚠️ | 40 |
| 1 | 0.96" **OLED** (I2C SSD1306) or phone screen | Gemma captions (EN/ML) | ✅ | 150 |
| 1 | WS2812 LED strip (8 px) | shows sighted judges what the wearer feels | ✅ | 100 |
| 1 | Wide elastic chest band (≈1 m × 8 cm) + 2 wrist cuffs + 2 finger rings (velcro) | garment | ⚠️ tailor/sports shop | 300 |
| – | 2‑core flexible wire, heat‑shrink, hot glue, sewing kit, zip ties | | ✅ | – |
| – | 3D‑printed motor pucks ×8, laser‑cut controller case | | ✅ TinkerSpace | – |

**Wearable total ≈ ₹2,500**

## Hub
| Part | Role | Note |
|---|---|---|
| Laptop (M‑series Mac ideal) or Raspberry Pi 5 8 GB | Ollama + **Gemma 3n E4B** (audio in) fully offline | Pi 5 = true edge; laptop = safe |
| **USB microphone** (or laptop mic for dev) | hears the melam | directional if possible |
| Phone / laptop hotspot named `spandanam-hub` | Wi‑Fi to wearable | no internet needed |
| Bluetooth/USB speaker | play melam recordings for the demo | |

## Demo props
- A chenda (borrow) or drums for a live melam; else curated melam recordings (Panchari full cycle, ~4 min) on the laptop.
- Earplugs + blindfold for judges to try it "deaf".

## Buy‑now list
8× coin/LRA vibration motors · LiPo 1000+ mAh + JST · TP4056 · elastic band + velcro · USB mic (if none) · ULN2003 if not in inventory.

## Software
- `ollama pull gemma3n:e4b` (≈7.5 GB — start immediately). Fallback `gemma3n:e2b`.
- Python 3.10+: `pip install -e "hub[dev]"`; `pip install soundfile` for `--wav` playback.
- Arduino IDE 2 + ESP32 core (no extra libs needed for the band).
- `GEMINI_API_KEY` from Google AI Studio for the post‑session report.
