from rich.panel import Panel
from rich.table import Table

from .config import MOTORS


def render(frame: bytes, hearing, levels: dict[str, float], preferences: str) -> Panel:
    t = Table.grid(padding=(0, 2))
    t.add_row(*[f"[bold]{m}[/]" for m in MOTORS])
    t.add_row(*[("█" * (v // 32)).ljust(8, "·") for v in frame[1:9]])
    lv = "  ".join(f"{b}:{v:.2f}" for b, v in levels.items())
    body = (f"{t}\n{lv}\n\n[cyan]{', '.join(hearing.instruments) or '—'}[/]  kaalam {hearing.kaalam}  "
            f"event [magenta]{hearing.event}[/]\n[bold]{hearing.caption_en}[/]\n{hearing.caption_ml}\n"
            f"[dim]prefs: {preferences}[/]")
    return Panel(body, title="Spandanam — feel the melam")
