import os
from dataclasses import dataclass, field

FINGERS = ("thumb", "index", "middle", "ring", "pinky")
FINGER_KEYS = {"j": 1, "k": 2, "l": 3, ";": 4, " ": 0}      # laptop keys emulate IMUs; finger 0 = real MPU6050
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

# Hit windows (ms) like a rhythm game
PERFECT_MS, GOOD_MS, MISS_MS = 40, 90, 180


@dataclass(frozen=True)
class Config:
    host: str = "0.0.0.0"
    port: int = 8000
    sample_rate: int = 22050
    # Point the Pi at a laptop running Ollama with: OLLAMA_URL=http://<laptop-ip>:11434  (rules allow laptop or edge)
    ollama_url: str = field(default_factory=lambda: os.environ.get("OLLAMA_URL", "http://127.0.0.1:11434"))
    gemma_model: str = field(default_factory=lambda: os.environ.get("GEMMA_MODEL", "gemma3n:e4b"))
    gemini_model: str = "gemini-2.5-flash"
    imu_strike_g: float = 2.5
    dry: bool = False
