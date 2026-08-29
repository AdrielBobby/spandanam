import pytest

librosa = pytest.importorskip("librosa")
sf = pytest.importorskip("soundfile")

from viral.synth_track import PATTERN, render
from viral.sound import SR
from viral.transcribe import onsets_to_beats, transcribe


def test_transcribe_synthetic_track_recovers_tempo_and_onsets(tmp_path):
    p = tmp_path / "t.wav"; sf.write(p, render(96, 2), SR)
    tr = transcribe(str(p))
    assert 80 <= tr.bpm <= 200                              # 96 or a multiple/half
    assert len(tr.onsets) >= len(PATTERN) * 2 * 0.7        # most hits found
    ev = onsets_to_beats(tr, 96)
    assert ev[0][0] == 0.0 and all(b % 0.25 == 0 for b, _, _ in ev)
    assert len(tr.cluster_profile) >= 3                    # several distinct timbres


def test_learn_cache_roundtrip(tmp_path, monkeypatch):
    import asyncio, json
    from viral import learn as L
    from viral.gemma_thaalam import default_structure
    p = tmp_path / "t.wav"; sf.write(p, render(96, 2), SR)
    calls = {"n": 0}
    async def fake_structure(client, url, model, bpm, profile, events, wav, fb):
        calls["n"] += 1; return default_structure(bpm, 16)
    monkeypatch.setattr(L, "structure", fake_structure)
    s1, st1 = asyncio.run(L.learn_from_file(p, "http://x", "m"))
    s2, st2 = asyncio.run(L.learn_from_file(p, "http://x", "m"))
    assert calls["n"] == 1 and s1.notes == s2.notes and st2.beats_per_cycle == st1.beats_per_cycle and st2.cluster_to_finger == st1.cluster_to_finger
    assert L._cache_path(p, "m").exists()
