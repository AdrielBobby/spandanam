import pytest

from asan.config import FINGERS, SYLLABLE_FINGER, SYLLABLES, validate_syllable_finger_mapping


def test_exactly_five_unique_fingers():
    assert len(FINGERS) == 5
    assert len(set(FINGERS)) == 5


def test_every_syllable_maps_to_one_valid_finger():
    for syl in SYLLABLES:
        assert syl in SYLLABLE_FINGER
        assert SYLLABLE_FINGER[syl] in FINGERS


def test_module_mapping_passes_validation():
    validate_syllable_finger_mapping(SYLLABLE_FINGER)  # should not raise


def test_validation_rejects_missing_syllable():
    incomplete = {s: f for s, f in SYLLABLE_FINGER.items() if s != "tha"}
    with pytest.raises(ValueError):
        validate_syllable_finger_mapping(incomplete)


def test_validation_rejects_unknown_finger():
    bad = dict(SYLLABLE_FINGER)
    bad["tha"] = "sixth_finger"
    with pytest.raises(ValueError):
        validate_syllable_finger_mapping(bad)
