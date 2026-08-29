import pytest

from viral.ladder import DEFAULT_SCALES, PASS_STARS, Ladder, advance


def test_default_ladder_starts_at_first_scale():
    ladder = Ladder()
    assert ladder.scales == DEFAULT_SCALES
    assert ladder.step == 0
    assert ladder.bpm_scale == DEFAULT_SCALES[0]
    assert ladder.total_steps == len(DEFAULT_SCALES)


def test_pass_advances_to_next_step():
    ladder = Ladder(step=0)
    result = advance(ladder, stars=PASS_STARS)
    assert result.event == "step_up"
    assert result.ladder is not None
    assert result.ladder.step == 1
    assert result.ladder.bpm_scale == DEFAULT_SCALES[1]


def test_pass_above_threshold_also_advances():
    result = advance(Ladder(step=0), stars=3)
    assert result.event == "step_up" and result.ladder.step == 1


def test_fail_stays_on_same_step():
    ladder = Ladder(step=1)
    result = advance(ladder, stars=PASS_STARS - 1)
    assert result.event == "retry"
    assert result.ladder == ladder  # unchanged, same object contents


def test_pass_on_last_step_completes_the_ladder():
    last = len(DEFAULT_SCALES) - 1
    result = advance(Ladder(step=last), stars=PASS_STARS)
    assert result.event == "complete"
    assert result.ladder is None


def test_fail_on_last_step_still_retries_not_completes():
    last = len(DEFAULT_SCALES) - 1
    result = advance(Ladder(step=last), stars=0)
    assert result.event == "retry"
    assert result.ladder is not None and result.ladder.step == last


def test_custom_scales_and_phrase_are_preserved_across_advance():
    ladder = Ladder(scales=(0.5, 1.0), phrase=2, step=0)
    result = advance(ladder, stars=PASS_STARS)
    assert result.ladder.scales == (0.5, 1.0)
    assert result.ladder.phrase == 2


def test_empty_scales_rejected():
    with pytest.raises(ValueError, match="non-empty"):
        Ladder(scales=())


def test_out_of_range_step_rejected():
    with pytest.raises(ValueError, match="out of range"):
        Ladder(step=99)
