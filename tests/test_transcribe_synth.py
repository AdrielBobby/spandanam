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
    assert len(tr.onsets) >= len(PATTERN) * 2 * 0.6        # most hits found
    ev = onsets_to_beats(tr, 96)
    assert ev[0][0] == 0.0 and all(b % 0.25 == 0 for b, _, _ in ev)
    assert len(tr.cluster_profile) >= 3                    # several distinct timbres


def test_learn_cache_roundtrip(tmp_path, monkeypatch):
    import asyncio, json
    from viral import learn as L
    from viral.gemma_thaalam import default_structure
    p = tmp_path / "t.wav"; sf.write(p, render(96, 2), SR)
    calls = {"n": 0}
    async def fake_structure(client, url, model, bpm, profile, events, wav, fb, *a):
        calls["n"] += 1; return default_structure(bpm, 16)
    monkeypatch.setattr(L, "structure", fake_structure)
    s1, st1 = asyncio.run(L.learn_from_file(p, "http://x", "m"))
    s2, st2 = asyncio.run(L.learn_from_file(p, "http://x", "m"))
    assert calls["n"] == 1 and s1.notes == s2.notes and st2.beats_per_cycle == st1.beats_per_cycle and st2.cluster_to_finger == st1.cluster_to_finger
    assert L._cache_path(p, "m").exists()


def test_reconcile_cycle_overrides_unrelated_gemma_cycle_when_evidence_strong():
    from viral.learn import reconcile_cycle
    from viral.gemma_thaalam import default_structure
    from dataclasses import replace
    st = replace(default_structure(96, 32), beats_per_cycle=12, thaalam="panchari (12)")
    out = reconcile_cycle(st, {4: 0.3, 6: 0.1, 8: 0.6, 12: 0.2, 16: 0.4}, 96)
    assert out.beats_per_cycle == 8 and "chempada" in out.thaalam and "cycle set to 8" in out.evidence
    weak = reconcile_cycle(st, {4: 0.1, 8: 0.12, 12: 0.05}, 96)
    assert weak.beats_per_cycle == 12                       # weak evidence: Gemma's call stands
    rel = reconcile_cycle(replace(st, beats_per_cycle=16), {8: 0.6, 16: 0.4}, 96)
    assert rel.beats_per_cycle == 16                        # related (2x) allowed


def test_normalize_octave_folds_fast_even_cycles(tmp_path):
    from viral.transcribe import transcribe, refine_tempo, normalize_octave, pick_cycle
    from viral.synth_track import render
    p = tmp_path / "t.wav"; sf.write(p, render(88, 4, "tabla"), SR)
    tr = transcribe(str(p)); bpm, sc = refine_tempo(tr); bpm2, sc2 = normalize_octave(tr, bpm, sc)
    assert bpm2 <= 160 and abs(bpm2 - 88) < 4 and pick_cycle(sc2) == 8


def test_reconcile_clamps_confidence_and_marks_uncertain():
    from viral.learn import reconcile_cycle
    from viral.gemma_thaalam import default_structure
    from dataclasses import replace
    st = replace(default_structure(96, 32), beats_per_cycle=8, confidence=0.9)
    weak = reconcile_cycle(st, {3: 0.05, 4: 0.1, 8: 0.08}, 96)
    assert weak.confidence <= 0.35 and "uncertain" in weak.thaalam
    mid = reconcile_cycle(st, {4: 0.2, 8: 0.25}, 96)
    assert mid.confidence == 0.5 and "uncertain" not in mid.thaalam
    strong = reconcile_cycle(st, {8: 0.7}, 96)
    assert strong.confidence == 0.9


def test_thin_events_merges_doublets_and_caps_density():
    from viral.learn import thin_events
    ev = [(0.0, 0, .5), (0.25, 0, .9), (0.5, 1, .4), (0.75, 1, .3), (1.0, 2, .9), (1.0, 3, .8), (1.0, 4, .7), (1.25, 2, .2)]
    out = thin_events(ev, {i: i for i in range(5)})
    beats0 = [e for e in out if e[1] == 0]; assert beats0 == [(0.25, 0, .9)]        # doublet merged, strongest kept
    assert len([e for e in out if int(e[0]) == 1]) <= 2                             # density cap


def test_build_kit_from_synthetic(tmp_path, monkeypatch):
    from viral import sample_kit
    from viral.transcribe import transcribe
    from viral.synth_track import render
    monkeypatch.setattr(sample_kit, "KITS_DIR", tmp_path / "kits")
    p = tmp_path / "t.wav"; sf.write(p, render(96, 2), SR)
    tr = transcribe(str(p))
    out = sample_kit.build_kit(p, tr, {i: i for i in range(5)}, "track_t")
    assert out is not None and all((out / f"{i}.wav").exists() for i in range(5))
