# Creative elements — pick, stack, show off

Each element is scoped for 24 h, says what hardware it needs, and — most important — what **only Gemma** does in it.

| # | Element | Fun | What only Gemma does | Hardware | Effort |
|---|---|---|---|---|---|
| 1 | **Vaaythari call‑and‑response** (core) — asan chants a phrase, taps it on your wrist, you play it back, asan corrects in Malayalam | ★★★★ | Hears drum audio → syllables; fuses IMU; diagnoses; speaks Malayalam | Pi, mic, IMU, 3 buzzers | done |
| 2 | **Composer asan** — every lesson Gemma *invents* a new phrase in the Panchari idiom for your weakness | ★★★★ | Generative composition under pedagogy rules | – | done (`teach()`) |
| 3 | **Talk to the asan** — "Asan, pathukke", "thakadhimi padippikku", "onnoode" | ★★★★ | Malayalam speech → intent, offline, same model | mic | done (`--voice`) |
| 4 | **Feel‑first mode (deaf learners)** — buzzers teach silently; Gemma judges from IMU + contact mic | ★★★★★ | Cross‑modal judgement without hearing | piezo contact mic | 2 h |
| 5 | **Kaalam ladder** — unlock Panchari's 5 tempo stages; the asan decides readiness, not a timer | ★★★★ | Readiness judgement from history | LED strip / OLED | 2 h |
| 6 | **Melam mode** — two students, two sticks: Gemma referees who leads/lags, who broke pattern | ★★★★★ | Multi‑player pattern reasoning | 2nd IMU | 3 h |
| 7 | **Guru personality** — warm, slightly strict Thrissur asan; praise is rare so it means something | ★★★ | Persona + culturally accurate idiom | – | 30 min |
| 8 | **Stick posture coach** — "your wrist drops on the left stroke, that's why it's weak" | ★★★★ | Explaining sound faults by motion | IMU (have) | 1 h |
| 9 | **Visible vaaythari** — screen shows asked vs heard syllables as a live diff | ★★★★ | The transcription *is* the content | HDMI/laptop | 1 h |
| 10 | **Onam mini‑game (Onakalikal)** — "Repeat after Maveli": longest correct chain wins; Gemma escalates + teases kindly | ★★★★★ | Adaptive difficulty + generated phrases + banter | – | 1.5 h |
| 11 | **Asan's notebook** (Gemini, cloud) — end‑of‑class report + tomorrow's plan to a parent's phone | ★★★ | Long‑context synthesis | internet once | done |
| 12 | **Haptic metronome that lets go** — buzzers hold tempo; Gemma decides when to stop holding your hand | ★★★ | Pedagogical judgement | buzzers | 1 h |

## Recommended stack for the demo
Core (1+2+3) → **9** (judges *see* Gemma's transcription) → **8** (IMU story) → **10** (midnight crowd game) → **5**. If a 2nd IMU appears, **6** is the wow.

## The Gemma‑only test
Ask of every feature: *could a threshold, lookup table, or classifier trained in 24 h do this?* If yes, it's DSP — keep it fast and don't credit Gemma. What survives:
- **Drum audio → vaaythari syllables** (no dataset exists; zero‑shot multimodal)
- **Explaining a sound fault by motion data** (cross‑modal reasoning)
- **Composing new drills under teaching rules** (generation)
- **Malayalam speech in / out, offline** (language)
- **Deciding readiness, difficulty, tone from a learner's history** (judgement + memory)

Beat timing, strike detection, tap scheduling stay deterministic — and we say so on stage. Judges trust teams that know the difference.
