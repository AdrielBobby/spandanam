from viral.bridge import phrase_to_score
from viral.score import Note, Score
from viral.server import chantable_syllables


def test_chantable_syllables_from_vaaythari_phrase():
    sc = phrase_to_score(["dhim", "tha", "ka"], 60)
    assert chantable_syllables(sc) == ("dhim", "tha", "ka")


def test_chantable_syllables_drops_unlabeled_notes():
    sc = Score("t", 60, 3, (Note(0, 0, 1.0, "dhim"), Note(1, 1, 1.0, ""), Note(2, 2, 1.0, "tha")))
    assert chantable_syllables(sc) == ("dhim", "tha")


def test_chantable_syllables_all_unlabeled_is_empty():
    sc = Score("t", 60, 2, (Note(0, 0), Note(1, 1)))   # label defaults to ""
    assert chantable_syllables(sc) == ()


def test_chantable_syllables_preserves_note_order_not_finger_order():
    sc = Score("t", 60, 3, (Note(0, 4, 1.0, "ki"), Note(1, 0, 1.0, "dhim"), Note(2, 2, 1.0, "ta")))
    assert chantable_syllables(sc) == ("ki", "dhim", "ta")
