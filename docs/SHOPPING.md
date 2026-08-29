# What to buy / borrow — 5-finger edition

We already have: **Pi 5, 1× MPU6050 IMU, 3× buzzers.** Target is **5 IMUs, 5 buzzers, 5 LEDs** (one channel per finger). Lists below are marked **[have]** / **[need]**.

## Must (today)
| Item | Have | Need | Why | Where |
|---|---|---|---|---|
| Pi 5 | 1 | — | hub | [have] |
| MPU6050 IMU | 1 | **4 more** (total 5) | one per finger | Robu / local electronics |
| Buzzer / coin vibration motor 3 V | 3 | **2 more** (total 5) | one per finger; buzzers are a stopgap, motors feel right | Robu / local |
| **TCA9548A I2C multiplexer** (or equivalent address‑expander) | 0 | 1 | all MPU6050s share the same default I2C address — 5 of them on one bus need a mux or AD0‑pin address switching. **This is a real build risk, budget time for it, don't discover it at 2 AM.** | TinkerSpace lab / electronics shop |
| **5× LEDs** (any color, or 1 addressable WS2812 strip of 5) | 0 | 5 | one per finger, for the finger‑lane dashboard mirror / Kaalam ladder | TinkerSpace / local |
| **USB microphone** (or USB sound card + lav mic) | 0 | 1 | Pi has no mic input; Gemma must hear | electronics shop / borrow laptop mic |
| **Speaker** (USB / 3.5 mm / BT) | 0 | 1 | Asan's voice | borrow |
| NPN 2N2222/S8050 + 1 kΩ + 1N4148 | 3 sets | **2 more sets** (5 total) | drive 5 buzzers from GPIO | TinkerSpace lab |
| Current‑limiting resistors for 5 LEDs | 0 | 5 | drive LEDs safely from GPIO | TinkerSpace lab |
| Glove or 5‑finger strap mounts | 0 | 1 set | mount 5 IMUs + 5 buzzers + 5 LEDs on one hand | fabric/velcro, TinkerSpace, or a cheap work glove |
| Jumper wires, breadboard, tape | some | more (5 channels wire up fast) | | TinkerSpace |
| **A chenda** or any drum + 2 sticks | 0 | 1 | demo on the real thing | borrow — TinkerHub / temple committee / music college |

## Should
| Item | Why |
|---|---|
| **2nd 5‑IMU glove** (5 more MPU6050 + mux + straps) | Melam mode (2 students) — the wow, now needs a full second finger rig, not just one spare IMU |
| **Piezo contact mic** (₹50) taped to the drum | Feel‑first mode + clean audio in a noisy hall |
| **OLED / HDMI screen** | 5‑lane visible vaaythari dashboard |
| **PD power bank 5 V 3 A+** | Pi wire‑free on stage, more current draw now with 5 buzzers + 5 LEDs |
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
