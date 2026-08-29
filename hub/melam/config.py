from dataclasses import dataclass, field


@dataclass(frozen=True)
class HubConfig:
    listen_host: str = "0.0.0.0"
    listen_port: int = 9000
    node_port: int = 9001
    sample_hz: int = 100
    # Strike detection
    strike_threshold_g: float = 3.0       # |accel| minus gravity, in g
    strike_refractory_s: float = 0.08     # min gap between strikes
    # Sync / tempo
    tempo_window_s: float = 4.0
    phase_tolerance_ms: float = 40.0
    # Fatigue
    fatigue_window_s: float = 30.0
    # Gemma (Ollama on this device)
    ollama_url: str = "http://127.0.0.1:11434"
    gemma_model: str = "gemma3n:e4b"      # multimodal (audio+text) on-device
    gemma_every_s: float = 2.0            # reasoning cadence
    # Gemini (cloud, post-session only)
    gemini_model: str = "gemini-2.5-flash"
    node_ids: tuple[str, ...] = field(default=("drummer-1", "drummer-2", "drummer-3", "drummer-4"))


# Panchari melam: 5 kaalams, tempo doubles each stage. Beats per cycle (thaalam) and nominal BPM.
PANCHARI_KAALAMS: tuple[dict, ...] = (
    {"name": "Pathikaalam", "cycle_beats": 96, "bpm": 20},
    {"name": "Randam kaalam", "cycle_beats": 48, "bpm": 40},
    {"name": "Moonnam kaalam", "cycle_beats": 24, "bpm": 80},
    {"name": "Naalam kaalam", "cycle_beats": 12, "bpm": 160},
    {"name": "Anchaam kaalam", "cycle_beats": 6, "bpm": 320},
)
