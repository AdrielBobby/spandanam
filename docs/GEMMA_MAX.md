# Maximising Gemma — practical notes (5-finger edition)

## Model
- **gemma3n:e4b** (Ollama) — audio + text in, ~8 GB RAM. Best quality. On Pi 5 8 GB expect 8–20 s per hearing — fine for a lesson loop, not for reflexes.
- **gemma3n:e2b** — ~2× faster on the Pi. Same API. Pull both now.
- Laptop hub is allowed by the rules; Pi 5 is the better *story*. Decide by 19:00 after timing one hearing on the Pi with all 5 IMU channels attached.

## Reliable JSON
`"format": "json"` + schema in the system prompt + `temperature ≤ 0.3` + `validate_syllables()` on the way in (already wired). Clips ≤ 4 s, 16 kHz mono. Always tell Gemma what was ASKED — comparison beats free transcription. The ASKED payload now includes the finger‑split phrase (which of the 5 fingers plays which syllable and when), not just a flat syllable string.

## Better hearing, cheaply
- Pass all **5 IMU streams** (one per finger: thumb, index, middle, ring, pinky) as hints — count + timing per finger — so syllable count anchors to real per‑finger hits instead of one aggregate stream.
- Map each finger to a core vaaythari bol in the system prompt (thumb = *thom*, open low · index = *nam* · middle = *ta* · ring = *ki* · pinky = *dhim*) so Gemma can say *which finger* was off, not just which syllable.
- Describe each syllable's timbre in the system prompt as before (tha = open right, ki = closed left…), now tagged with its finger.
- Add 2 few‑shot (asked, 5×imu → played) examples after tonight's first real recordings — five timing arrays instead of one.

## Speech
- TTS: `sudo apt install espeak-ng` (has `ml`). Piper voice if one is available offline. macOS dev: `say`.
- STT: none — Gemma 3n hears the request directly (`intent()`). Talking point: one model is both ears and brain.

## Latency budget per turn
Fusing 5 IMU channels instead of 1 doesn't change the model's latency math — it's still one multimodal call, just with a slightly larger structured input. Budget stays: chant+tap 2–4 s → student 2–4 s → hear 5–15 s → speak 2 s → teach 3–6 s ≈ 25 s. Fill Gemma time with the 5‑lane dashboard animating so it never feels idle.

## Stage line
"Timing is math; we don't pretend it's AI. Gemma does the four things no threshold can: hear which syllables you played on which finger, explain the weak one using that finger's motion, compose your next drill, and talk to you in Malayalam — on this Pi, offline."
