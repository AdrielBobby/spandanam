from viral.malayalam import coach_ml, structure_ml, FINGERS_ML, LABELS_ML


def test_coach_ml_mentions_fingers_error_and_drill():
    s = coach_ml(62.5, "wrong_finger", ["ring", "middle"], ["ka"], 72, 1)
    assert "മോതിരവിരൽ" in s and "നടുവിരൽ" in s and "തെറ്റായ വിരൽ" in s and "72 bpm" in s and "2-ാം ഭാഗം" in s
    assert "63%" in s


def test_coach_ml_perfect_and_no_phrase():
    s = coach_ml(96, "none", [], [], 100, None)
    assert "വളരെ നന്നായി" in s and "വീണ്ടും വായിക്കൂ" in s


def test_structure_ml_confidence_words():
    assert "ഉറപ്പാണ്" in structure_ml("chempada (8)", 8, 60, 0.8)
    assert "ഊഹം" in structure_ml("x", 3, 10, 0.35)
    assert LABELS_ML["ashaan_says"] == "ആശാൻ പറയുന്നു" and len(FINGERS_ML) == 5
