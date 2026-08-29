"""Asan console: live rich table of every drummer."""
from __future__ import annotations

from rich.table import Table

from .fatigue import FatigueFeatures
from .sync import NodeTempo

FATIGUE_STYLE = {"fresh": "green", "tiring": "yellow", "risk": "bold red"}


def render(tempos: list[NodeTempo], offsets_ms: dict[str, float], fatigue: dict[str, FatigueFeatures],
           decision: dict | None, kaalam: int, note: str) -> Table:
    t = Table(title=f"Melam Asan — kaalam {kaalam}  ·  {note}")
    for col in ("drummer", "bpm", "offset ms", "jitter ms", "HR", "HR slope", "amp decay %", "fatigue", "reason"):
        t.add_column(col)
    for nt in tempos:
        f = fatigue.get(nt.node)
        d = (decision or {}).get(nt.node, {})
        fat = d.get("fatigue", "-")
        off = offsets_ms.get(nt.node, 0.0)
        off_style = "green" if abs(off) < 40 else "yellow" if abs(off) < 100 else "red"
        t.add_row(nt.node, f"{nt.bpm:.0f}", f"[{off_style}]{off:+.0f}[/]", f"{nt.jitter_ms:.0f}",
                  f"{f.hr_bpm:.0f}" if f else "-", f"{f.hr_slope_bpm_per_min:+.1f}" if f else "-",
                  f"{f.amp_decay_pct:.0f}" if f else "-",
                  f"[{FATIGUE_STYLE.get(fat, 'white')}]{fat}[/]", d.get("reason", ""))
    return t
