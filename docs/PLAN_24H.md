# 24 h plan — Vaaythari (5-finger edition)

| Time | Milestone |
|---|---|
| 15:30–16:30 | Pi: Ollama + gemma3n pulls, espeak‑ng, I2C on + **TCA9548A mux wired** (5× MPU6050 share one address). Buy the 4 extra IMUs, 2 extra buzzers, 5 LEDs, glove/strap. |
| 16:30–18:30 | `python -m asan.main --dry --lang en` on laptop with 1 finger channel live: chant → tap → student taps back → Gemma hears → next lesson. Solder/crimp the other 4 finger channels in parallel. |
| **19:00 CP1** | All 5 IMUs reading through the mux, 5 buzzers and 5 LEDs addressable individually from the Pi. No Gemma yet — just deterministic tap-through-tap loopback per finger. |
| 19:00–23:30 | Glove/strap assembly (5 finger IMU pockets + 5 buzzer pads + 5 LEDs). Gemini call wired up to generate a short Panchari phrase; Gemma splits it into a 5-finger tap sequence. Prompt tuning on a real chenda (few‑shot). `--voice` Malayalam intents. Dashboard: 5 finger lanes live. |
| **23:30 CP2** | Full 5-finger loop end‑to‑end: Gemini phrase → Gemma finger-split → buzzers chant it finger‑by‑finger → student taps the glove → dashboard lanes show asked vs heard per finger → Gemma corrects the weak finger in Malayalam. Demo with a teammate who's never played. |
| 00:30–03:00 | Onakalikal game (#10), posture coach per finger (#8), guru persona (#7). Midnight crowd test — let a stranger wear the glove. |
| 03:00–06:00 | Robustness: mux glitches, buzzer crosstalk, glove strap comfort, thermal, battery. Kaalam ladder LEDs (now literally 5 finger LEDs) if time. Sleep in shifts. |
| 06:00–08:00 | Gemini notebook report (now summarizes per-finger accuracy, not just overall). |
| **08:00 CP3** | Dress rehearsal, timed, glove on a volunteer's hand who hasn't tried it before. |
| 09:00–12:00 | README/docs final, 90 s video, repo tidy. |
| **13:30** | Submit. |

## Demo script (3 min)
1. "Chenda has been taught for 500 years by voice — vaaythari. Our asan does it the same way, but now it listens to each finger separately, on a Pi, offline." Adriel wears the glove — 5 IMUs, 5 buzzers, 5 LEDs, one per finger.
2. Gemini generates a short Panchari phrase for Adriel's level; Gemma splits it into 5 finger taps. The asan chants *dhim‑tha‑ka* while the glove buzzes thumb‑index‑middle in sequence; Adriel taps it back finger by finger; the laptop dashboard shows 5 lanes — asked vs heard, live, Yousician‑style.
3. Fathima: "Asan, pathukke" → tempo drops across all 5 lanes. "Thakadhimi padippikku" → Gemini/Gemma generate a new phrase.
4. Adriel drops his ring finger late on purpose → asan blames that one finger's IMU timing, not the whole hand. Sound + per-finger motion fused, diagnosis is finger-specific.
5. Game mode: a judge wears the glove, repeats phrases until they fail a finger; Gemma escalates, teases kindly, per-finger streaks shown on the dashboard.
6. Pull Wi‑Fi — nothing changes, all 5 channels keep running locally. Show the Gemini notebook (now a per-finger progress report) on a phone.
