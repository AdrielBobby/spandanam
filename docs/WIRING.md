# Wiring — Pi 5 (BCM numbering)

| Finger | Buzzer/motor GPIO | LED GPIO | Colour |
|---|---|---|---|
| 0 thumb | 18 | 5 | red |
| 1 index | 13 | 6 | orange |
| 2 middle | 12 | 22 | yellow |
| 3 ring | 19 | 23 | green |
| 4 pinky | 16 | 24 | blue |

- Buzzer/motor: GPIO → 100 Ω → buzzer (+), (−) → GND. Coin motors > 40 mA: GPIO → 1 kΩ → NPN base, motor between 3V3/5V and collector, 1N4148 across motor.
- LED: GPIO → 220 Ω → LED → GND.
- MPU6050 (thumb, today's only real IMU): VCC 3V3 · GND · SDA GPIO2 (pin 3) · SCL GPIO3 (pin 5). Enable I2C.
- Speaker: 3.5 mm / USB / Bluetooth. Set default sink with `raspi-config` or `wpctl`.
- Glove: surgical glove for support; hot‑glue LED + buzzer pucks on fingertips, IMU on the thumb's first joint, wires along the back of the hand to a wrist cuff → ribbon to the Pi.

Emulated fingers: laptop keys **SPACE J K L ;** in the dashboard map to thumb…pinky and produce the same `Strike` events as the IMU.
