# Architecture

```
 drummer-1  ┐  XIAO ESP32-S3 + MPU6050 (stick) + MAX30102 (wrist) + vibra motor
 drummer-2  ┼──── Wi-Fi UDP JSON @100 Hz ────►  HUB (laptop / Raspberry Pi 5)
 drummer-3  ┘  ◄── single-char haptic cmds ──   ├─ ingest.py     Sense
 asan (opt) ─┘                                   ├─ strike.py     stroke onsets (threshold+hysteresis+refractory)
 USB mic ────── 2 s WAV clips ──────────────────►├─ sync.py       tempo, phase offset vs reference, haptic cue
                                                 ├─ fatigue.py    HR slope, amplitude decay, jitter growth
                                                 ├─ gemma_coach   ON-DEVICE Gemma 3n (Ollama): kaalam state,
                                                 │                 pattern breaks, fatigue grade + reason  Think
                                                 ├─ haptics.py    F/S/R/K commands, rate-limited          Act
                                                 └─ console.py    live asan table
 after session:  session.json + video ──► gemini_report.py (Gemini API, cloud) ──► report.md
```

## Why the split
| Layer | Tool | Why |
|---|---|---|
| Beat timing, phase error | DSP | Deterministic, <10 ms, no model needed |
| Musical state (which kaalam, who broke pattern), fatigue judgement with rationale | **Gemma 3n on-device** | Needs pattern reasoning + audio; must work at a temple ground with no internet; drummer biometrics stay local |
| Coaching report, video analysis | **Gemini API** | Heavy multimodal reasoning once per session |

## Sense → Think → Act loop (per 10 ms sample)
1. Parse UDP sample → `Sample` (immutable).
2. `detect_strike` → strike events per node.
3. Every loop: tempo/offset/fatigue features (pure functions).
4. Every 2 s: prompt Gemma with fused JSON (+ audio) → `CoachDecision` JSON.
5. Act: `F` (lagging → faster), `S` (rushing → slower), `R` (rest, risk), `K` (kaalam change) → node vibration motor.

## Hardware removal test
Remove the IMUs → no strikes → no tempo, no phase, no Gemma input, no haptics. The product ceases to exist. ✔
