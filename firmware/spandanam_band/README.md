# spandanam_band firmware
XIAO ESP32-S3 driving 8 coin/LRA vibration motors through a ULN2003 (or 2× TB6612) — each motor on its own PWM channel so intensity is continuous, not on/off.

| idx | body site | why |
|---|---|---|
| 0 | chest | valanthala (bass chenda) |
| 1 | back | valanthala accent / kalasham |
| 2,3 | wrists | idanthala (treble chenda) |
| 4,5 | shoulders | kombu / kuzhal (horns, sustained) |
| 6,7 | fingers | elathalam (cymbals) |

Wiring: XIAO GPIO1–8 → ULN2003 IN1–7 (+1 more transistor for the 8th), motors between ULN outputs and +3.7 V, common diode. LiPo on BAT pads. Sew motors into a wide elastic band + two wrist cuffs.

Flash: `cp config.h.example config.h`, set the hub hotspot, board *XIAO_ESP32S3*. Band does a chest→wrists hello pulse when connected.
