"""Build the default 'chenda' kit from REAL recordings: pick the cleanest isolated strike per role from source tracks.

  python -m viral.build_chenda_kit            # writes assets/kits/chenda/0..4.wav (+ preview on ~/Desktop if --preview)

Roles → sources (cluster = timbre rank, 0 = lowest):
  0 valanthala (bass head)      solo_thayambaka          lowest cluster
  1 idanthala open (ringing)    solo_takita_sadhakam     low-mid cluster
  2 idanthala closed (damped)   solo_takita_sadhakam     mid cluster
  3 rim / stick edge            solo_takita_sadhakam     brightest cluster
  4 elathalam (cymbal)          panchari_traditional_ensemble  brightest cluster
Samples are local-only (git-ignored) — derived from third-party recordings for the hackathon demo.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np

from .sample_kit import KITS_DIR, shape_sample
from .transcribe import transcribe

TRACKS = Path(__file__).resolve().parents[2] / "assets" / "tracks"
ROLES = [  # finger, source, cluster-rank selector (0 lowest .. 4 brightest), max length s, release fraction
    (0, "solo_thayambaka.wav", 0, 1.2, 0.5),
    (1, "solo_takita_sadhakam.wav", 1, 0.8, 0.45),
    (2, "solo_takita_sadhakam.wav", 2, 0.35, 0.4),
    (3, "solo_takita_sadhakam.wav", 4, 0.25, 0.4),
    (4, "panchari_traditional_ensemble.wav", 4, 1.4, 0.55),
]


def best_strike(tr, cluster: int, y: np.ndarray, sr: int, top: int = 8) -> float:
    """Among the most isolated onsets of this cluster, choose the one with the cleanest attack (highest peak/RMS ratio)."""
    times = np.array([o.t_s for o in tr.onsets]); end = len(y) / sr
    cands = []
    for i, o in enumerate(tr.onsets):
        if o.cluster != cluster or o.t_s > end - 1.5 or o.t_s < 0.3:      # skip clip edges (fade-outs masquerade as isolation)
            continue
        others = np.delete(times, i); iso = float(np.min(np.abs(others - o.t_s))) if others.size else 9.0
        if iso < 0.06:
            continue
        cands.append((iso, o.strength, o.t_s))
    cands.sort(reverse=True)
    best, best_q = None, -1.0
    for iso, strength, t in cands[:top]:
        i0 = int(t * sr); seg = y[i0:i0 + int(0.15 * sr)]
        if seg.size < 100: continue
        q = float(np.abs(seg).max() / (np.sqrt(np.mean(seg ** 2)) + 1e-9)) * min(iso, 0.8) * (0.5 + strength)
        if q > best_q: best_q, best = q, t
    if best is None and cands:
        return cands[0][2]
    if best is None:                                            # nothing isolated at all: take the strongest hit away from the edges
        inner = [o for o in tr.onsets if o.cluster == cluster and 0.3 < o.t_s < end - 1.5]
        return max(inner, key=lambda o: o.strength).t_s if inner else 0.5
    return best


def build(preview: bool = False) -> Path:
    import librosa, soundfile as sf
    out = KITS_DIR / "chenda"; out.mkdir(parents=True, exist_ok=True)
    cache: dict[str, tuple] = {}
    for finger, src, rank, max_len, rel in ROLES:
        p = TRACKS / src
        if src not in cache:
            tr = transcribe(str(p)); y, sr = librosa.load(str(p), sr=22050, mono=True); cache[src] = (tr, y, sr)
        tr, y, sr = cache[src]
        ranks = sorted(tr.cluster_profile, key=lambda c: tr.cluster_profile[c]["centroid_hz"])
        cluster = ranks[min(rank, len(ranks) - 1)]
        t = best_strike(tr, cluster, y, sr)
        times = np.array(sorted(o.t_s for o in tr.onsets)); nxt = times[times > t + 0.02]
        length = float(np.clip((nxt[0] - t - 0.015) if nxt.size else max_len, 0.2, max_len))
        i0 = max(0, int((t - 0.003) * sr)); n = int(length * sr); seg = y[i0:i0 + n]
        if seg.size < n: seg = np.pad(seg, (0, n - seg.size))
        seg = shape_sample(seg, sr, release_frac=rel)
        sf.write(out / f"{finger}.wav", (seg / (np.abs(seg).max() or 1) * 0.9).astype(np.float32), sr)
        print(f"finger {finger}: {src} cluster {cluster} ({tr.cluster_profile[cluster]['centroid_hz']:.0f} Hz) @ {t:.2f}s len {length:.2f}s")
    if preview:
        from .sound import Sampler, SR
        smp = Sampler("chenda"); beat = 0.6
        pat = [0, 2, 1, 2, 0, 3, 1, 4, 0, 2, 1, 2, 0, 3, 4, 4]
        total = int(SR * (5 * 1.0 + len(pat) * beat / 2 + 2)); mix = np.zeros(total, dtype=np.float32)
        seq = [(i * 1.0, i) for i in range(5)] + [(5 + i * beat / 2, v) for i, v in enumerate(pat)]
        for t0, v in seq:
            i = int(t0 * SR); w = smp.buf[v]; mix[i:i + len(w)] += w[: max(0, total - i)] * 0.8
        dst = Path.home() / "Desktop" / "thaalam_samples" / "kit_previews" / "chenda_real.wav"
        sf.write(dst, mix / (np.abs(mix).max() or 1) * 0.9, SR); print("preview:", dst)
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--preview", action="store_true"); a = ap.parse_args()
    build(a.preview)
