"""Audio -> percussive note events (deterministic). Onsets + timbre features + 5-way clustering + tempo.
Gemma later decides WHICH cluster goes to WHICH finger and what the thaalam is."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class Onset:
    t_s: float
    cluster: int
    strength: float
    centroid_hz: float


@dataclass(frozen=True)
class Transcription:
    bpm: float
    onsets: tuple[Onset, ...]
    cluster_profile: dict[int, dict]      # cluster -> {"centroid_hz", "count", "mean_strength"}
    duration_s: float


def kmeans_1d(x: np.ndarray, k: int, iters: int = 30) -> np.ndarray:
    """Tiny deterministic k-means on log-centroid so 5 timbres -> 5 fingers (low→high)."""
    if x.size == 0:
        return np.array([], dtype=int)
    k = min(k, max(1, len(np.unique(x))))
    cents = np.quantile(x, np.linspace(0.1, 0.9, k))
    for _ in range(iters):
        lab = np.argmin(np.abs(x[:, None] - cents[None, :]), axis=1)
        new = np.array([x[lab == j].mean() if np.any(lab == j) else cents[j] for j in range(k)])
        if np.allclose(new, cents): break
        cents = new
    order = np.argsort(cents)                      # cluster 0 = lowest timbre (thumb), 4 = brightest (pinky)
    remap = {int(o): i for i, o in enumerate(order)}
    return np.array([remap[int(l)] for l in lab])


def transcribe(path: str, k: int = 5) -> Transcription:
    import librosa
    y, sr = librosa.load(path, sr=22050, mono=True)
    y_h, y_p = librosa.effects.hpss(y)             # keep the percussive part
    onset_env = librosa.onset.onset_strength(y=y_p, sr=sr)
    frames = librosa.onset.onset_detect(onset_envelope=onset_env, sr=sr, backtrack=False, units="frames")
    tempo, _ = librosa.beat.beat_track(onset_envelope=onset_env, sr=sr)
    times = librosa.frames_to_time(frames, sr=sr)
    cent = librosa.feature.spectral_centroid(y=y_p, sr=sr)[0]
    c_at = np.array([cent[min(f, len(cent) - 1)] for f in frames]) if len(frames) else np.array([])
    strength = np.array([onset_env[min(f, len(onset_env) - 1)] for f in frames]) if len(frames) else np.array([])
    strength = strength / strength.max() if strength.size and strength.max() > 0 else strength
    labels = kmeans_1d(np.log1p(c_at), k) if c_at.size else np.array([], dtype=int)
    onsets = tuple(Onset(float(t), int(l), float(s), float(c)) for t, l, s, c in zip(times, labels, strength, c_at))
    prof = {}
    for j in range(k):
        sel = [o for o in onsets if o.cluster == j]
        if sel:
            prof[j] = {"centroid_hz": round(float(np.mean([o.centroid_hz for o in sel])), 1), "count": len(sel),
                       "mean_strength": round(float(np.mean([o.strength for o in sel])), 2)}
    bpm = float(np.atleast_1d(tempo)[0]) if np.atleast_1d(tempo).size else 90.0
    return Transcription(bpm, onsets, prof, float(len(y) / sr))


def onsets_to_beats(tr: Transcription, bpm: float, grid: float = 0.25) -> list[tuple[float, int, float]]:
    """(beat, cluster, strength) quantised to the grid, relative to the first onset."""
    if not tr.onsets:
        return []
    t0 = tr.onsets[0].t_s; beat_s = 60.0 / bpm
    return [(round((o.t_s - t0) / beat_s / grid) * grid, o.cluster, o.strength) for o in tr.onsets]


# ---------- compact musical digest for the model (deterministic) ----------
GRID = 0.25
CYCLE_CANDIDATES = (4, 6, 7, 8, 12, 14, 16)


def cycle_scores(events: list[tuple[float, int, float]], candidates=CYCLE_CANDIDATES) -> dict[int, float]:
    """How periodic is the onset pattern at each cycle length (beats)? Autocorrelation of the onset grid, 0..1."""
    if len(events) < 8:
        return {c: 0.0 for c in candidates}
    n = int(round(max(b for b, _, _ in events) / GRID)) + 2
    grid = np.zeros(n)
    for b, _, s in events:
        grid[int(round(b / GRID))] = max(grid[int(round(b / GRID))], s)
    grid = grid - grid.mean()
    denom = float(np.dot(grid, grid)) or 1.0
    out = {}
    for c in candidates:
        lag = int(c / GRID)
        out[c] = round(max(0.0, float(np.dot(grid[:-lag], grid[lag:])) / denom), 3) if lag < n else 0.0
    return out


def beat_histogram(events: list[tuple[float, int, float]], cycle: int) -> dict[int, list[int]]:
    """Per cluster: how many hits land on each beat position (whole beats) within the given cycle."""
    hist = {}
    for b, c, _ in events:
        pos = int(b % cycle)
        hist.setdefault(c, [0] * cycle)[pos] += 1
    return hist


def cycle_table(events: list[tuple[float, int, float]]) -> dict[str, dict[int, float]]:
    """Periodicity at half, original and double tempo — melam tempo estimates are often off by 2×."""
    out = {}
    for label, k in (("half_tempo", 0.5), ("tempo", 1.0), ("double_tempo", 2.0)):
        scaled = [(b * k, c, s) for b, c, s in events]
        out[label] = cycle_scores(scaled, (6, 7, 8, 12, 14, 16))
    return out


def digest(bpm: float, profile: dict, events: list[tuple[float, int, float]], head: int = 32,
           scores: dict[int, float] | None = None) -> dict:
    """What Gemma actually reads: small, structured, evidence-rich. `scores` = per-timbre periodicity (preferred)."""
    cs = scores if scores is not None else cluster_cycle_scores(events)
    mx = max(cs.values()) if cs else 0.0
    best = pick_cycle(cs)
    return {
        "bpm": round(bpm, 1),
        "n_events": len(events),
        "clusters": {str(k): v for k, v in profile.items()},
        "cycle_periodicity": {str(k): v for k, v in cs.items()},
        "cycle_periodicity_by_tempo": {lab: {str(k): v for k, v in tbl.items()} for lab, tbl in cycle_table(events).items()},
        "best_cycle_guess": best,
        "evidence_strength": "strong" if mx > 0.35 else "weak" if mx > 0.12 else "very weak",
        "note": "cycle_periodicity = per-timbre autocorrelation at the refined tempo; sub-multiples of the true cycle also score high",
        "beat_histogram_at_best_cycle": {str(k): v for k, v in beat_histogram(events, best).items()},
        "opening_pattern": " ".join(f"{b:g}:{c}" for b, c, _ in events[:head]),
    }


# ---------- per-timbre periodicity + tempo refinement (the discriminative version) ----------
CYCLE_CANDIDATES_V2 = (4, 6, 7, 8, 12, 14, 16)


def quantize_onsets(tr: Transcription, bpm: float, grid: float = GRID) -> list[tuple[float, int, float]]:
    if not tr.onsets:
        return []
    t0 = tr.onsets[0].t_s; beat = 60.0 / bpm
    return [(round((o.t_s - t0) / beat / grid) * grid, o.cluster, o.strength) for o in tr.onsets]


def cluster_cycle_scores(events: list[tuple[float, int, float]], candidates=CYCLE_CANDIDATES_V2) -> dict[int, float]:
    """Periodicity of WHICH timbre hits WHERE: autocorrelation per cluster grid, count-weighted average. 0..1.
    Unlike the plain onset grid this is not dominated by the beat pulse, so cycle lengths separate."""
    if len(events) < 8:
        return {c: 0.0 for c in candidates}
    n = int(round(max(b for b, _, _ in events) / GRID)) + 2
    out = {c: 0.0 for c in candidates}; wsum = 0.0
    for k in {c for _, c, _ in events}:
        g = np.zeros(n)
        for b, c, s in events:
            if c == k:
                i = int(round(b / GRID)); g[i] = max(g[i], s)
        gm = g - g.mean(); den = float(gm @ gm) or 1.0; w = float((g > 0).sum())
        for c in candidates:
            lag = int(c / GRID)
            if lag < n:
                out[c] += w * max(0.0, float(gm[:-lag] @ gm[lag:]) / den)
        wsum += w
    return {c: round(v / wsum, 3) if wsum else 0.0 for c, v in out.items()}


def refine_tempo(tr: Transcription, octaves=(0.5, 1.0, 2.0), spread: float = 0.05, steps: int = 41) -> tuple[float, dict[int, float]]:
    """Search tempo octaves × ±spread for the bpm whose grid makes the timbre pattern most periodic.
    Fixes the two classic failures: octave errors and a 1–3 % tempo drift that destroys long-lag correlation."""
    best = None
    for k in octaves:
        for r in np.linspace(1 - spread, 1 + spread, steps):
            bpm = tr.bpm * k * r
            if not 40 <= bpm <= 240:
                continue
            cs = cluster_cycle_scores(quantize_onsets(tr, bpm))
            adj = max(cs.values()) - 0.06 * abs(np.log2(k))
            if best is None or adj > best[0]:
                best = (adj, float(bpm), cs)
    return (best[1], best[2]) if best else (tr.bpm, cluster_cycle_scores(quantize_onsets(tr, tr.bpm)))


def pick_cycle(scores: dict[int, float], tolerance: float = 0.85) -> int:
    """Shortest cycle within `tolerance` of the best score: the true period; its multiples are trivially periodic too."""
    mx = max(scores.values()) if scores else 0.0
    return min((c for c, v in scores.items() if v >= tolerance * mx), default=8) if mx > 0 else 8


def normalize_octave(tr: Transcription, bpm: float, scores: dict[int, float], max_bpm: float = 160.0) -> tuple[float, dict[int, float]]:
    """Melam is counted at a walking/moderate pulse. If the refined tempo is very fast and the winning cycle is even,
    fold one octave down (176 bpm × 16 → 88 bpm × 8). Scores are recomputed at the folded tempo."""
    while bpm > max_bpm and pick_cycle(scores) % 2 == 0:
        bpm /= 2
        scores = cluster_cycle_scores(quantize_onsets(tr, bpm))
    return bpm, scores
