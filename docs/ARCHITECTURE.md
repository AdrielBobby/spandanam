# Architecture

```
 melam (live or recording) ──► USB mic ──► HUB (laptop / Pi 5)
                                          ├─ audio.py   10 ms hops + rolling 2 s buffer          Sense
                                          ├─ dsp.py     band energies (bass/treble/horn/cymbal),
                                          │             adaptive gain, onsets @100 Hz            Think (reflex)
                                          ├─ gemma_ear  GEMMA 3n ON-DEVICE, every 2 s, hears the clip:
                                          │             instruments playing, kaalam, events,
                                          │             body_map + gains (how to FEEL it),
                                          │             motif for events, EN/ML caption          Think (judgement)
                                          ├─ haptic.py  compose 8-motor frame = levels × map × gains
                                          │             + onset kick + motif  ──► UDP 'S'+8 bytes   Act
                                          └─ console.py live body view + captions
 WEARABLE: XIAO ESP32-S3 + ULN2003 + 8 vibration motors (chest, back, wrists, shoulders, fingertips) + OLED
 after: session.json ──► gemini_report.py (Gemini API) ──► report.md
```

## Why both layers
| Layer | Does | Why not the other |
|---|---|---|
| DSP @100 Hz | turn energy in a band into vibration *now* (<20 ms) | a model is too slow for tactile latency |
| Gemma 3n @0.5 Hz | decide *what* is playing and *how it should be felt*: routes instruments to body sites, scales gains for the section, fires event motifs, writes captions, applies listener preferences | band energy ≠ instrument (kombu and idanthala overlap); kaalam/kalasham/solo are musical concepts, not spectral ones; preferences are natural language |

Remove Gemma → a loudness vest (mush). Remove the wearable → nothing to feel. Both tests pass.

## Frame protocol
`'S'` + 8 × uint8 intensity, motor order = `config.MOTORS`. Band cuts all motors 300 ms after the last frame.
