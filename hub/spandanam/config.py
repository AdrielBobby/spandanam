from dataclasses import dataclass

MOTORS = ("chest", "back", "l_wrist", "r_wrist", "l_shoulder", "r_shoulder", "l_finger", "r_finger")

# Frequency bands (Hz) the fast path tracks. Chenda bass ~80-250, treble ~300-1200, cymbals >3000, horns 400-2000 sustained.
BANDS = {"bass": (60, 250), "treble": (300, 1200), "horn": (400, 2000), "cymbal": (3000, 9000)}

# Default routing: band -> motors, before Gemma personalises it.
DEFAULT_MAP = {"bass": ("chest", "back"), "treble": ("l_wrist", "r_wrist"),
               "horn": ("l_shoulder", "r_shoulder"), "cymbal": ("l_finger", "r_finger")}


@dataclass(frozen=True)
class HubConfig:
    sample_rate: int = 16000
    hop_ms: int = 10                 # fast path frame rate (100 Hz)
    band_host: str = "192.168.4.2"   # band's IP on the hotspot (or broadcast)
    band_port: int = 9001
    ollama_url: str = "http://127.0.0.1:11434"
    gemma_model: str = "gemma3n:e4b"
    gemma_clip_s: float = 2.0
    gemini_model: str = "gemini-2.5-flash"
    max_intensity: int = 255
