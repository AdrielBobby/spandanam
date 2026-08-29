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
