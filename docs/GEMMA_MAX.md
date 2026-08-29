# Maximising Gemma — practical notes

## Model
- **gemma3n:e4b** (Ollama) — audio + text in, ~8 GB RAM. Best quality. On Pi 5 8 GB expect 8–20 s per hearing — fine for a lesson loop, not for reflexes.
- **gemma3n:e2b** — ~2× faster on the Pi. Same API. Pull both now.
- Laptop hub is allowed by the rules; Pi 5 is the better *story*. Decide by 19:00 after timing one hearing on the Pi.

## Reliable JSON
`"format": "json"` + schema in the system prompt + `temperature ≤ 0.3` + `validate_syllables()` on the way in (already wired). Clips ≤ 4 s, 16 kHz mono. Always tell Gemma what was ASKED — comparison beats free transcription.

## Better hearing, cheaply
- Pass IMU strokes (count + timing) as hints so syllable count anchors to real hits.
- Describe each syllable's timbre in the system prompt (tha = open right, ki = closed left…).
- Add 2 few‑shot (asked, imu → played) examples after tonight's first real recordings.

## Speech
- TTS: `sudo apt install espeak-ng` (has `ml`). Piper voice if one is available offline. macOS dev: `say`.
- STT: none — Gemma 3n hears the request directly (`intent()`). Talking point: one model is both ears and brain.

## Latency budget per turn
chant+tap 2–4 s → student 2–4 s → hear 5–15 s → speak 2 s → teach 3–6 s ≈ 25 s. Fill Gemma time with the Visible‑vaaythari screen animating so it never feels idle.

## Stage line
"Timing is math; we don't pretend it's AI. Gemma does the four things no threshold can: hear which syllables you played, explain the weak one using the stick's motion, compose your next drill, and talk to you in Malayalam — on this Pi, offline."
