# Creative elements — pick, stack, show off (5-finger edition)

Each element is scoped for 24 h, says what hardware it needs, and — most important — what **only Gemma** does in it.

| # | Element | Fun | What only Gemma does | Hardware | Effort |
|---|---|---|---|---|---|
| 1 | **Vaaythari call‑and‑response** (core) — Gemini generates a phrase, asan chants it and taps it out finger‑by‑finger on the glove, you tap it back, asan corrects the weak finger in Malayalam | ★★★★ | Hears drum audio → syllables; fuses 5 IMU streams; diagnoses which finger; speaks Malayalam | Pi, mic, 5 IMUs, 5 buzzers | done |
| 2 | **Composer asan** — every lesson Gemini/Gemma *invent* a new phrase in the Panchari idiom for your weakest finger | ★★★★ | Generative composition under pedagogy rules, targeted at one finger | – | done (`teach()`) |
| 3 | **Talk to the asan** — "Asan, pathukke", "thakadhimi padippikku", "onnoode" | ★★★★ | Malayalam speech → intent, offline, same model | mic | done (`--voice`) |
| 4 | **Feel‑first mode (deaf learners)** — buzzers teach silently, one per finger; Gemma judges from 5 IMU streams + contact mic | ★★★★★ | Cross‑modal judgement across 5 channels without hearing | piezo contact mic | 2 h |
| 5 | **Kaalam ladder** — unlock Panchari's 5 tempo stages; the asan decides readiness per finger, not a timer | ★★★★ | Readiness judgement from per‑finger history | 5× finger LEDs | 2 h |
| 6 | **Melam mode** — two students, two gloves: Gemma referees who leads/lags, and *which finger* broke the pattern | ★★★★★ | Multi‑player, multi‑finger pattern reasoning | 2nd 5‑IMU glove | 3 h |
| 7 | **Guru personality** — warm, slightly strict Thrissur asan; praise is rare so it means something | ★★★ | Persona + culturally accurate idiom | – | 30 min |
| 8 | **Finger posture coach** — "your ring finger drops late, that's why *ki* is weak" | ★★★★ | Explaining a specific finger's sound fault by its own motion | 5 IMUs (have 1, need 4 more) | 1 h |
| 9 | **Visible vaaythari (5 lanes)** — Yousician‑style dashboard: 5 finger lanes show asked vs heard syllables as a live diff, one lane per finger, LEDs mirror the active lane | ★★★★ | The per‑finger transcription *is* the content | HDMI/laptop, 5 LEDs | 1.5 h |
| 10 | **Onam mini‑game (Onakalikal)** — "Repeat after Maveli": longest correct 5‑finger chain wins; Gemma escalates + teases kindly | ★★★★★ | Adaptive difficulty + generated phrases + banter, tracked per finger | – | 1.5 h |
| 11 | **Asan's notebook** (Gemini, cloud) — end‑of‑class report per finger + tomorrow's plan to a parent's phone | ★★★ | Long‑context synthesis across 5 finger histories | internet once | done |
| 12 | **Haptic metronome that lets go** — 5 buzzers hold tempo per finger; Gemma decides when to stop holding your hand | ★★★ | Pedagogical judgement, per finger | 5 buzzers | 1 h |

## Recommended stack for the demo
Core (1+2+3) → **9** (judges *see* Gemma's per‑finger transcription across 5 lanes) → **8** (finger‑specific IMU story) → **10** (midnight crowd game) → **5**. If a 2nd glove appears, **6** is the wow.

## The Gemma‑only test
Ask of every feature: *could a threshold, lookup table, or classifier trained in 24 h do this?* If yes, it's DSP — keep it fast and don't credit Gemma. What survives:
- **Drum audio → vaaythari syllables, per finger** (no dataset exists; zero‑shot multimodal)
- **Explaining a sound fault by one finger's motion data** (cross‑modal reasoning, now with 5 candidate channels instead of 1)
- **Composing new drills under teaching rules, targeted at a weak finger** (generation)
- **Malayalam speech in / out, offline** (language)
- **Deciding readiness, difficulty, tone from a learner's per‑finger history** (judgement + memory)

Beat timing, strike/tap detection per finger, and buzzer/LED scheduling stay deterministic across all 5 channels — and we say so on stage. Judges trust teams that know the difference.
