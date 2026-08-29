# 24 h plan — Spandanam

| Time | Milestone |
|---|---|
| 14:30–15:30 | Pull gemma3n:e4b. Collect XIAO, ULN2003, OLED, LED strip; buy 8 motors, LiPo, elastic band. |
| 15:30–17:30 | Hub: `python -m spandanam.main --wav melam.wav` + `python -m spandanam.fake_band` → bars move to the music. Gemma returns valid JSON with captions. |
| 17:30–19:00 | Band: XIAO + ULN2003 + 4 motors on breadboard, receiving frames. |
| **19:00 CP1** | Feel the bass on one motor from a recording. |
| 19:00–23:30 | All 8 motors, sewn into band + cuffs. Gemma body_map/gains actually change routing. Onset kick tuned. |
| **23:30 CP2** | Wear it, eyes closed, earplugs: can you tell chenda from cymbals from kombu? Fix mapping until yes. |
| 00:30–03:00 | Event motifs (kaalam change / kalasham). OLED captions EN/ML. LED strip mirror. Preferences via `--prefs`. |
| 03:00–06:00 | Live mic with a real drum. Latency check. Battery test. 3D‑print motor pucks. Sleep in shifts. |
| 06:00–08:00 | Gemini report end‑to‑end. |
| **08:00 CP3** | Full 3‑min demo run‑through. |
| 09:00–12:00 | README, BOM final, video (judge wearing band, screen showing body map + captions, then Wi‑Fi off). |
| 12:30 / **13:30** | Final checkpoint / submit. |

## Demo script (3 min)
1. "Melam is the sound of Onam. 2–3 lakh Malayalis have never heard it." Hand the judge the band + earplugs.
2. Play Panchari from pathikaalam. Screen shows body map: bass on chest, cymbals on fingers. Judge nods on the beat.
3. Kombu enters → shoulders hum, caption "കൊമ്പ് — horns join". Kaalam doubles → 3‑pulse wrists.
4. Judge says "softer chest, more cymbals" → `--prefs` → Gemma re‑maps live.
5. Kalasham → everything rises, back motif. Pull Wi‑Fi: still running. Show Gemini report on phone.
