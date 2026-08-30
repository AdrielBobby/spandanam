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


def test_stop_survives_missing_pkill(monkeypatch):
    """No pkill on Windows, and check=False does not swallow a missing executable. stop()
    runs on startup via start_free -> stop_all, so raising here takes the whole server down."""
    from viral import speech
    monkeypatch.setattr(speech.shutil, "which", lambda _name: None)
    speech.stop()           # must not raise
