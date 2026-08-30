from viral.speech import SYL_DEVA, _chant_text, chant_voice


def test_devanagari_mapping_covers_core_syllables():
    for s in ("tha", "ki", "ta", "ka", "dhi", "mi", "dhim", "thom", "num", "ri"):
        assert s in SYL_DEVA
    assert _chant_text(("tha", "ki", "ta"), True) == "ता कि ट" and _chant_text(("tha", "ki"), False) == "tha ki"


def test_voice_override(monkeypatch):
    monkeypatch.setenv("THAALAM_VOICE", "Rishi"); assert chant_voice() == ("Rishi", False)
    monkeypatch.setenv("THAALAM_VOICE", "Lekha"); assert chant_voice() == ("Lekha", True)


def test_stop_clears_active_and_does_not_raise():
    from viral import speech
    speech._ACTIVE.append(type("P", (), {"kill": lambda self: None})())
    speech.stop(); assert speech._ACTIVE == []
