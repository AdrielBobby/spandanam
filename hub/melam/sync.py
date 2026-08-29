"""Tempo and inter-drummer phase metrics from strike timestamps."""
from __future__ import annotations

from dataclasses import dataclass
from statistics import median


@dataclass(frozen=True)
class NodeTempo:
    node: str
    bpm: float
    jitter_ms: float
    strikes: int


def tempo_from_strikes(node: str, t_us: list[int]) -> NodeTempo:
    if len(t_us) < 3:
        return NodeTempo(node, 0.0, 0.0, len(t_us))
    ioi = [(b - a) / 1e3 for a, b in zip(t_us, t_us[1:])]  # ms
    med = median(ioi)
    jitter = median(abs(x - med) for x in ioi)
    return NodeTempo(node, 60_000.0 / med if med > 0 else 0.0, jitter, len(t_us))


def phase_offset_ms(ref_strikes_us: list[int], node_strikes_us: list[int]) -> float:
    """Median signed offset of node strikes to nearest reference strike (+ = late)."""
    if not ref_strikes_us or not node_strikes_us:
        return 0.0
    offsets = []
    for t in node_strikes_us:
        nearest = min(ref_strikes_us, key=lambda r: abs(r - t))
        offsets.append((t - nearest) / 1e3)
    return median(offsets)


def haptic_cue(offset_ms: float, tolerance_ms: float) -> str | None:
    """Map phase error to a node command: 'F' faster (lagging), 'S' slower (rushing), None in tolerance."""
    if offset_ms > tolerance_ms:
        return "F"
    if offset_ms < -tolerance_ms:
        return "S"
    return None


def group_reference(strikes_by_node: dict[str, list[int]]) -> list[int]:
    """Reference beat = the asan node if present, else the drummer with the most strikes."""
    if "asan" in strikes_by_node and strikes_by_node["asan"]:
        return strikes_by_node["asan"]
    return max(strikes_by_node.values(), key=len, default=[])
