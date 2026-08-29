# What to buy / borrow (beyond Pi 5 · 1 IMU · 3 buzzers)

## Must (today)
| Item | Qty | Why | Where |
|---|---|---|---|
| **USB microphone** (or USB sound card + lav mic) | 1 | Pi has no mic input; Gemma must hear | electronics shop / borrow laptop mic |
| **Speaker** (USB / 3.5 mm / BT) | 1 | Asan's voice | borrow |
| **Coin vibration motors 3 V** | 3–6 | Buzzers are a stopgap; motors feel right | Robu / local |
| **NPN 2N2222/S8050 + 1 kΩ + 1N4148** | 3–6 | Drive motors from GPIO | TinkerSpace lab |
| Jumper wires, breadboard, velcro wrist strap, tape | – | | TinkerSpace |
| **A chenda** or any drum + 2 sticks | 1 | Demo on the real thing | borrow — TinkerHub / temple committee / music college |

## Should
| Item | Why |
|---|---|
| **2nd MPU6050** | Melam mode (2 students) — the wow |
| **Piezo contact mic** (₹50) taped to the drum | Feel‑first mode + clean audio in a noisy hall |
| **OLED / HDMI screen** | Visible vaaythari diff |
| **WS2812 LED strip** | Kaalam ladder |
| **PD power bank 5 V 3 A+** | Pi wire‑free on stage |
| **Pi 5 active cooler** | Gemma will throttle without it |

## Nice
Kasavu cloth for the table, a pookalam printout as the asan's seat, earplugs for the deaf‑mode demo.

## Software now
```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama pull gemma3n:e4b; ollama pull gemma3n:e2b
sudo apt install -y espeak-ng portaudio19-dev i2c-tools
sudo raspi-config nonint do_i2c 0
cd hub && pip install -e ".[dev]"
```
