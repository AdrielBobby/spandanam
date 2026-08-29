# melam_node firmware

One node per drummer: XIAO ESP32-S3 + MPU6050 (stick or wrist) + MAX30102 (wrist, optional) + coin vibration motor.

## Libraries (Arduino Library Manager)
- Adafruit MPU6050, Adafruit Unified Sensor
- SparkFun MAX3010x Pulse and Proximity Sensor Library

## Wiring (XIAO ESP32-S3)
| Part | Pin |
|---|---|
| MPU6050 SDA / SCL | D4 / D5 (I2C) |
| MAX30102 SDA / SCL | D4 / D5 (shared I2C) |
| Vibration motor (via 2N2222 + 1k base resistor, flyback diode) | D3 |
| Status LED | D4-equivalent GPIO 4 (or onboard LED) |
| 3.7 V LiPo | BAT+/BAT- pads |

## Flash
1. `cp config.h.example config.h`, set `NODE_ID` and hub Wi‑Fi.
2. Board: *XIAO_ESP32S3*, upload.
3. Node buzzes once on boot when connected.
