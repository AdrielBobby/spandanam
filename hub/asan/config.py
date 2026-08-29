from dataclasses import dataclass

# Haptic zones on the student's wrist (3 buzzers today; coin motors later)
ZONES = ("right", "left", "accent")

# Chenda vaaythari syllables and which hand plays them (simplified teaching convention)
SYLLABLES = {
    "tha": "right", "ki": "left", "ta": "right", "ka": "left",
    "dhi": "right", "mi": "left", "dhim": "right", "thom": "right", "num": "left", "ri": "left",
}
ACCENT_SYLLABLES = {"dhim", "thom"}

# --- 5-finger hardware model (prototype) --------------------------------------------
# One IMU + buzzer + LED channel per finger. This syllable->finger grouping is a first
# guess for the hackathon build, not a musicological claim — expect to revise it after
# wearing the glove and testing with a real player.
FINGERS = ("thumb", "index", "middle", "ring", "pinky")

SYLLABLE_FINGER = {
    "thom": "thumb", "dhim": "thumb",
    "tha": "index", "dhi": "index",
    "ta": "middle",
    "ki": "ring", "ka": "ring",
    "mi": "pinky", "num": "pinky", "ri": "pinky",
}


def validate_syllable_finger_mapping(mapping: dict[str, str]) -> None:
    """Raise ValueError unless every syllable in SYLLABLES has a finger assignment in FINGERS."""
    missing = sorted(s for s in SYLLABLES if s not in mapping)
    if missing:
        raise ValueError(f"missing finger assignment for syllables: {missing}")
    unknown = sorted({f for f in mapping.values() if f not in FINGERS})
    if unknown:
        raise ValueError(f"unknown finger name(s): {unknown}")


validate_syllable_finger_mapping(SYLLABLE_FINGER)

# Starter phrases (the asan composes new ones beyond these)
SEED_PHRASES = {
    "thakita": ["tha", "ki", "ta"],
    "thakadhimi": ["tha", "ka", "dhi", "mi"],
    "dhimthakathakita": ["dhim", "tha", "ka", "tha", "ki", "ta"],
}

BANDS = {"bass": (60, 250), "treble": (300, 1200), "horn": (400, 2000), "cymbal": (3000, 9000)}


@dataclass(frozen=True)
class AsanConfig:
    sample_rate: int = 16000
    hop_ms: int = 10
    ollama_url: str = "http://127.0.0.1:11434"
    gemma_model: str = "gemma3n:e4b"     # e2b on a Pi 5 if e4b is too slow
    gemini_model: str = "gemini-2.5-flash"
    start_bpm: float = 60.0
    tap_ms: int = 60                     # buzzer pulse per syllable
    listen_pad_s: float = 0.6            # extra time after the phrase to catch late strokes
    imu_strike_g: float = 2.5
    language: str = "ml"                 # asan speaks Malayalam; "en" fallback
