# Spandanam 🥁✋

**Feel the chenda melam.** A haptic wearable that lets deaf and hard‑of‑hearing people experience Kerala's loudest art form — with **Gemma 3n running on‑device** as the ears that decide *how* the music should be felt.

Built in 24 h at the [Google Physical AI Hackathon: Onam Edition](https://physicalai.tinkerhub.org/), TinkerSpace Kochi, 29–30 Aug 2026 · Themes: **Homecoming (care & accessibility) · Onakalikal** · Powered by Gemma + Gemini.

## The problem
Onam without melam is unthinkable — yet Kerala's 2–3 lakh deaf and hard‑of‑hearing people stand in the crowd and feel only a blur. Existing "music vests" map loudness to buzz; a melam through that is noise.

## Sense → Think → Act
| | |
|---|---|
| **Sense** | A microphone on the hub hears the live ensemble. |
| **Think — reflex** | DSP splits the sound into bass / treble / horn / cymbal energy at 100 Hz and fires vibrations within 20 ms. |
| **Think — judgement** | **Gemma 3n, offline, every 2 s, listens to the clip** and decides: which instruments are actually playing (valanthala, idanthala, elathalam, kombu, kuzhal), which *kaalam* we're in, whether a kombu solo or the *kalasham* climax is starting — then writes the **haptic score**: which body sites each instrument goes to, how strong, what motif marks an event, and a caption in English + Malayalam. It also honours the wearer's preferences in plain language ("softer chest, more cymbals"). |
| **Act** | 8 vibration motors — chest, back, both wrists, both shoulders, both fingertips — driven by PWM on a XIAO ESP32‑S3. OLED shows the captions; an LED strip mirrors the body map for sighted people. |

After the performance, the **Gemini API** turns the session log into a report on how the piece was felt and how to improve the mapping.

**Removal tests:** no wearable → nothing to feel. No Gemma → a loudness vest. Both fail, as they should.

## Why Gemma *on‑device*
- Temple grounds and festival crowds have no reliable connectivity.
- Latency: 2 s musical re‑planning next to a 10 ms reflex loop needs the model beside the DSP.
- Gemma 3n hears audio natively, so instrument identity, kaalam and climax — musical concepts a spectrum can't express — are decided locally, continuously, for free.

## Repo
```
firmware/spandanam_band/   XIAO ESP32-S3: 8-channel PWM haptic band, UDP frames
hub/spandanam/             audio · dsp (reflex) · gemma_ear (judgement) · haptic (frame composer) · console · gemini_report
hub/spandanam/fake_band.py dev stand-in for the wearable
tests/                     pytest
docs/                      BOM · ARCHITECTURE · PLAN_24H
```

## Quick start
```bash
brew install ollama            # or curl -fsSL https://ollama.com/install.sh | sh
ollama pull gemma3n:e4b        # fallback: gemma3n:e2b
cd hub && pip install -e ".[dev]" soundfile

python -m spandanam.fake_band                     # terminal 1: pretend wearable
python -m spandanam.main --band 127.0.0.1 --wav ../assets/panchari.wav   # terminal 2: from a recording
python -m spandanam.main --prefs "softer chest, more cymbals"            # live mic, real band

# post-session report
GEMINI_API_KEY=... python -c "from spandanam.gemini_report import *; from pathlib import Path; \
  print(generate_report(Path('data/sessions/<id>/session.json'), 'gemini-2.5-flash'))"
```
Wearable build: [`firmware/spandanam_band/README.md`](firmware/spandanam_band/README.md) · Parts: [`docs/BOM.md`](docs/BOM.md).

## Tests
```bash
cd hub && pytest
```

## Team
- Ryyan Safar — [@ryyansafar](https://github.com/ryyansafar)
- Adriel Bobby — [@AdrielBobby](https://github.com/AdrielBobby)
- Fathima Moonam Kandathil — [@fathima-004](https://github.com/fathima-004)

## Socials & Support
- Portfolio: https://ryyansafar.site
- GitHub: https://github.com/ryyansafar
- Buy Me a Coffee: https://buymeacoffee.com/ryyansafar
- PayPal: https://www.paypal.com/paypalme/ryyansafar
- Razorpay: https://razorpay.me/@ryyansafar

## License
MIT — see [LICENSE](LICENSE).
