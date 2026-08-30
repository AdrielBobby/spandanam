import os
from dataclasses import dataclass, field

FINGERS = ("thumb", "index", "middle", "ring", "pinky")
FINGER_KEYS = {"j": 1, "k": 2, "l": 3, ";": 4, " ": 0}      # laptop keys emulate IMUs
IMU_FINGER = 2   # which finger the single MPU6050 is physically mounted on (0=thumb .. 4=pinky)
FINGER_COLORS = ("#ff3b30", "#ff9500", "#ffd60a", "#34c759", "#0a84ff")

# Pi 5 GPIO (BCM). Buzzers on PWM-capable pins, LEDs on plain GPIO.
BUZZER_PINS = (18, 13, 12, 19, 16)
LED_PINS = (5, 6, 22, 23, 24)

KITS = {
    "chenda":    {"name": "Chenda",    "voices": ["valanthala", "idanthala-open", "idanthala-closed", "rim", "roll"]},
    "mridangam": {"name": "Mridangam", "voices": ["thom", "nam", "dhin", "chapu", "arai"]},
    "tabla":     {"name": "Tabla",     "voices": ["ge", "na", "tin", "te", "ke"]},
    "kit":       {"name": "Drum kit",  "voices": ["kick", "snare", "hihat", "tom", "ride"]},
}

# Hit windows (ms) like a rhythm game. Humans on a laptop keyboard + browser render add ~30–60 ms of jitter,
# so these are a little wider than a hardware controller would need.
PERFECT_MS, GOOD_MS, MISS_MS = 60, 120, 220
# Constant input latency to subtract from every strike (keyboard/USB/browser). Tune with INPUT_OFFSET_MS=… ; 0 = off.
INPUT_OFFSET_MS = float(os.environ.get("INPUT_OFFSET_MS", "0"))


def parse_engines(spec: str | None) -> dict[str, dict]:
    """GEMMA_ENGINES="laptop=http://127.0.0.1:11435|gemma3n:e4b,pi=http://127.0.0.1:11434|gemma3:1b" -> {name: {url, model}}"""
    out: dict[str, dict] = {}
    for part in (spec or "").split(","):
        if "=" in part and "|" in part:
            name, rest = part.split("=", 1); url, model = rest.rsplit("|", 1)
            out[name.strip()] = {"url": url.strip(), "model": model.strip()}
    return out


@dataclass(frozen=True)
class Config:
    host: str = "0.0.0.0"
    port: int = 8000
    sample_rate: int = 22050
    # Point the Pi at a laptop running Ollama with: OLLAMA_URL=http://<laptop-ip>:11434  (rules allow laptop or edge)
    ollama_url: str = field(default_factory=lambda: os.environ.get("OLLAMA_URL", "http://127.0.0.1:11434"))
    gemma_model: str = field(default_factory=lambda: os.environ.get("GEMMA_MODEL", "gemma3n:e4b"))
    gemini_model: str = field(default_factory=lambda: os.environ.get("GEMINI_MODEL", "gemini-3.6-flash"))
    imu_strike_g: float = field(default_factory=lambda: float(os.environ.get("IMU_STRIKE_G", "1.5")))
    dry: bool = False
    gemma_engines: dict = field(default_factory=lambda: parse_engines(os.environ.get("GEMMA_ENGINES")))
