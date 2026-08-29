# 24‑hour plan (Aug 29 14:00 → Aug 30 13:30 IST)

| Time | Milestone | Owner |
|---|---|---|
| 14:00–15:00 | Pull `gemma3n:e4b` on hub. Collect XIAO ×3, IMU ×3, motors. Buy MAX30102/LiPo/vibra if missing. | all |
| 15:00–17:00 | Node 1: IMU streaming to hub over hotspot. `simulate.py` drives hub meanwhile. | HW / SW |
| 17:00–19:00 | Strike detection tuned on a real stick. Haptic `F/S` works on Node 1. Gemma returns valid JSON. | |
| **19:00 CP1** | 1 drummer, live tempo, buzz when off‑beat. | |
| 19:00–23:30 | Nodes 2–3 built. Phase offsets between drummers. HR sensor integrated. Console table. | |
| **23:30 CP2** | 3 drummers in sync mode, Gemma grading fatigue, `R` command. | |
| 00:30–03:00 | Mic → Gemma 3n audio; kaalam detection; `K` cue. Laser‑cut wrist pucks + stick clips. | |
| 03:00–06:00 | Robustness: reconnects, packet loss, battery. Record session data. Sleep in shifts. | |
| 06:00–08:00 | Gemini report end‑to‑end on a recorded session. | |
| **08:00 CP3** | Full demo run‑through, timed at 3 min. | |
| 09:00–12:00 | README polish, BOM final, architecture diagram, 90 s demo video (3 drummers, cues visible, console on screen). | |
| 12:30 | Final checkpoint. Push everything. | |
| **13:30** | Submission closes. | |

## Demo script (3 min)
1. 10 s: "Chenda melam troupes play 6–8 h in Kerala heat; novices lose sync, seniors collapse. Meet the Asan."
2. Three of us drum. Console shows sync bars. Fathima deliberately lags → wrist buzzes → she corrects live.
3. Ryyan speeds up → Gemma announces kaalam change → all wrists triple‑buzz.
4. Show simulated fatigue (or real after 2 min hard drumming): HR climbing + amplitude decay → "risk" → long buzz + red row. Gemma's one‑line reason on screen.
5. Pull the Wi‑Fi: everything still runs — on‑device Gemma. Then show Gemini's post‑session report on the phone.
