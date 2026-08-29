# 24 h plan — Vaaythari

| Time | Milestone |
|---|---|
| 15:30–16:30 | Pi: Ollama + gemma3n pulls, espeak‑ng, I2C on. Buy mic/speaker/motors. |
| 16:30–18:30 | `python -m asan.main --dry --lang en` on laptop: chant → record → Gemma hears → next lesson. Time one hearing on the Pi. |
| **19:00 CP1** | Full loop on Pi: buzzers tap, IMU strokes counted, Gemma corrects. |
| 19:00–23:30 | Wrist strap + stick IMU mount. Prompt tuning on a real drum (few‑shot). `--voice` Malayalam intents. Visible vaaythari screen. |
| **23:30 CP2** | 3‑min lesson demo end‑to‑end with a teammate who's never played. |
| 00:30–03:00 | Onakalikal game (#10), posture coach (#8), guru persona (#7). Midnight crowd test. |
| 03:00–06:00 | Robustness, thermal, battery. Kaalam ladder LEDs if time. Sleep in shifts. |
| 06:00–08:00 | Gemini notebook report. |
| **08:00 CP3** | Dress rehearsal, timed. |
| 09:00–12:00 | README/docs final, 90 s video, repo tidy. |
| **13:30** | Submit. |

## Demo script (3 min)
1. "Chenda has been taught for 500 years by voice — vaaythari. Our asan does it the same way, on a Pi, offline." Adriel at the chenda, wrist strap on, IMU on the stick.
2. Asan chants *dhim‑tha‑ka*, buzzers tap R‑L; Adriel plays; screen shows heard vs asked; asan corrects in Malayalam.
3. Fathima: "Asan, pathukke" → tempo drops. "Thakadhimi padippikku" → new phrase.
4. Adriel drops his wrist on purpose → asan blames wrist angle (IMU). Sound + motion fused.
5. Game mode: a judge repeats phrases until they fail; Gemma escalates, teases kindly.
6. Pull Wi‑Fi — nothing changes. Show the Gemini notebook on a phone.
