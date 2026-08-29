# Maximising Gemma — practical notes

## Where Gemma sits
- `structure()` — once per uploaded track: bpm + 5 timbre clusters + quantised events (+ 6 s audio clip) → thaalam, cycle, finger map, syllables, phrases, kaalam. ~10–30 s on Pi 5 with e4b. Fill the wait with the "transcribing…" status and the pads lighting each cluster.
- `coach()` — once per practice attempt: summary JSON → 30‑word Malayalam + English feedback and the next drill. ~5–10 s.
- Never in the hit‑judging path. Judging is <1 ms math and stays that way.

## Model
`gemma3n:e4b` for quality (audio in). `gemma3n:e2b` if the Pi is slow. Pull both now. Laptop hub is allowed by the rules; Pi is the better story — time one `structure()` on the Pi by 19:00 and decide.

## Reliable JSON
`format: json`, schema in the system prompt, temperature 0.2, and every field validated/clamped in `parse_structure()` with a deterministic fallback (`default_structure`). The app never breaks if Gemma is slow or wrong.

## Making structure() smarter cheaply
- Clusters are ordered low→high timbre so "bass = thumb" is a sane default Gemma only has to override.
- Send ≤ 240 events; for long tracks send the first 2 cycles and let Gemma extrapolate the cycle.
- After tonight's first real tracks, add 2 few‑shot examples (input stats → good structure) to `STRUCT_SYS`.
- Pass the audio clip: instrument identity (chenda vs tabla) is far more reliable from sound than from centroid numbers.

## Speech
`coach()` returns `say_ml`; pipe it through espeak‑ng (`-v ml`) or Piper for a spoken asan. Optional, 20 lines.

## Stage line
"Every hit is judged by math in under a millisecond — we don't dress that up as AI. Gemma does what math can't: it listens to a track and understands it as a thaalam, decides how it lives on five fingers, cuts it into lessons, and coaches you in Malayalam — on this Pi, offline. Gemini writes new music for it."

## Pi 5 has 4 GB RAM — use the laptop's Gemma over a tunnel
`gemma3n:e4b` needs ~8 GB; `e2b` is borderline and slow on the Pi. The rules allow the model on a laptop, so:
```bash
# laptop (keeps running):   ./scripts/mac_gemma_tunnel.sh ryyan@<pi-ip>
# pi:                       ./scripts/pi_run.sh            # auto-detects the tunnel, else falls back to local e2b
```
Measured from the Pi through the tunnel to an M-series Mac: coach ≈ 7 s, structure ≈ 10–20 s. Same code path as fully on-Pi; only `OLLAMA_URL` changes.
Judging-day plan: laptop Gemma via tunnel for speed; show `ollama ps` on the laptop and the Pi's `OLLAMA_URL` so it's transparent. If e2b finishes and runs acceptably, demo one round fully on the Pi.
