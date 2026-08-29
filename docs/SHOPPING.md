# What to buy / borrow (have: Pi 5 · 1 MPU6050 · 3 buzzers · surgical gloves · laptops)

## Must (today)
| Item | Qty | Why |
|---|---|---|
| **Speaker** (3.5 mm / USB / BT) | 1 | the instrument comes out of it |
| **Buzzers** (to make 5) or **coin vibration motors 3 V** | 2–5 | tempo + cue on every finger; motors feel better than buzzers |
| **5 mm LEDs** (red, orange, yellow, green, blue) + 220 Ω | 5 | finger cue colours |
| NPN 2N2222/S8050 + 1 kΩ + 1N4148 | 5 | drive motors from GPIO |
| Thin flexible wire, hot glue, velcro wrist cuff, tape | – | glove build |
| Breadboard + jumpers | 1 | |

## Should
| Item | Why |
|---|---|
| **4× MPU6050** | real IMU on every finger (replaces keyboard emulation) — biggest upgrade |
| **PCA9548 I2C mux** or use MPU6050 AD0 for 2 addresses + a 2nd I2C bus | 5 IMUs on one Pi |
| **USB mic** | Gemma can *hear* the uploaded track live from the room / practice on a real drum |
| PD power bank 5 V 3 A+, Pi 5 active cooler | stage‑ready, Gemma won't throttle |
| Small HDMI display or tablet | dashboard beside the player |

## Nice
WS2812 strip along the back of the hand, kasavu cloth table, a real chenda to compare sounds.

## Software now
```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama pull gemma3n:e4b; ollama pull gemma3n:e2b
sudo apt install -y libportaudio2 libsndfile1 i2c-tools ffmpeg
sudo raspi-config nonint do_i2c 0
cd hub && pip install -e ".[dev]"
```
