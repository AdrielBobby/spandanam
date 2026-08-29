# Spandanam / Vaaythari

Onam-focused Kerala Chenda vaaythari learning coach.

- **Event:** Google Physical AI Hackathon: Onam Edition
- **Venue/dates:** TinkerSpace Kochi, 29–30 August 2026
- **Team:** Ryyan Safar, Adriel Bobby, Fathima Moonam Kandathil

## Architecture

- **Gemini (cloud)** — generates short Panchari-vaaythari practice exercises.
- **Gemma (local, laptop or Pi)** — explanation, arrangement, hearing/judging, Malayalam interaction, pedagogical adaptation.
- **Interface:** 5 finger lanes — thumb, index, middle, ring, pinky.
- **Hardware target:** 5× MPU6050 IMUs, 5× buzzers/vibration motors, 5× LEDs, glove/finger-strap rig, Raspberry Pi 5, laptop speakers, laptop dashboard.
- **Existing hardware:** Raspberry Pi 5, 1× MPU6050, 3× buzzers. Everything else not yet available. MPU6050 sensors and other glove components are still to be acquired.


## Current development constraints

- Develop on a Windows laptop first.
- The Pi has not yet been configured for use.
- No MPU6050 sensors are currently available for testing.
- Until hardware arrives, use a keyboard-based simulator as the input source.
- Do not add GPIO, I2C, real-IMU, multiplexer, or Pi-only requirements to laptop development tasks.

## Engineering boundaries

- Deterministic code owns beat timing, event scheduling, input normalization, scoring, LED/buzzer timing, and safety limits.
- Gemini/Gemma must not control millisecond-level feedback loops.
- Every input source normalizes events to: `timestamp_ms, finger, source, strength`.
- Preserve the old single-IMU code path until the five-finger path is tested.
- Keep changes small, reversible, and independently testable.
- Run tests after each change and report the exact command/result.
- Do not commit without explicit user approval.
- Do not expose, store, or commit API keys or secrets.
- Do not install large dependencies or call external APIs without asking.
