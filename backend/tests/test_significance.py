"""Tests for the A/B significance test.

This is the one piece of arithmetic in the system that can be silently wrong
and still look right. A miscomputed p-value does not crash; it produces a
confident sentence recommending a subject line on the strength of a coin toss,
and someone acts on it.

The refusals matter as much as the calculation. On a list of a few hundred,
declining to name a winner is usually the correct answer, and a dashboard that
always picks one is lying with statistics.
"""
import pytest

from app.services.stats_service import (
    MIN_EVENTS_FOR_SIGNIFICANCE, MIN_GROUP_FOR_SIGNIFICANCE,
    SIGNIFICANCE_THRESHOLD, ab_verdict, two_proportion_p_value,
)


# --- the calculation ----------------------------------------------------------


def test_identical_rates_give_no_evidence_of_difference():
    p = two_proportion_p_value(50, 100, 50, 100)
    assert p == pytest.approx(1.0)


def test_a_large_clear_difference_is_significant():
    """60% against 40% on 100 each. Hand-checked: pooled 0.5, standard error
    0.0707, z 2.83, two-sided p about 0.0047."""
    p = two_proportion_p_value(60, 100, 40, 100)
    assert p == pytest.approx(0.0047, abs=0.0005)
    assert p < SIGNIFICANCE_THRESHOLD


def test_a_small_difference_on_small_groups_is_not_significant():
    """11 against 9 out of 120 each — the shape of a real result on this
    company's list, and one that means nothing."""
    p = two_proportion_p_value(11, 120, 9, 120)
    assert p > SIGNIFICANCE_THRESHOLD


def test_the_test_is_symmetric():
    """Which variant is called A must not change the answer."""
    assert two_proportion_p_value(30, 100, 20, 100) == pytest.approx(
        two_proportion_p_value(20, 100, 30, 100)
    )


def test_p_value_is_always_a_probability():
    for x1, n1, x2, n2 in [(1, 10, 9, 10), (0, 50, 1, 50), (25, 50, 26, 50)]:
        p = two_proportion_p_value(x1, n1, x2, n2)
        assert p is not None and 0.0 <= p <= 1.0


@pytest.mark.parametrize(
    "args",
    [
        (0, 0, 0, 0),      # no data at all
        (5, 0, 5, 10),     # an empty group
        (0, 50, 0, 50),    # nobody engaged: pooled rate zero, no standard error
        (50, 50, 50, 50),  # everybody did: pooled rate one
    ],
)
def test_degenerate_inputs_return_none_rather_than_dividing_by_zero(args):
    assert two_proportion_p_value(*args) is None


# --- the refusals -------------------------------------------------------------


def test_small_groups_are_refused_before_any_arithmetic():
    """Below the group minimum the answer is "we cannot tell", regardless of
    how lopsided the numbers happen to look."""
    result = ab_verdict(10, 20, 2, 20)
    assert result["p_value"] is None
    assert result["significant"] is False
    assert "Not enough recipients" in result["verdict"]


def test_large_groups_with_almost_no_engagement_are_refused():
    n = MIN_GROUP_FOR_SIGNIFICANCE + 10
    result = ab_verdict(1, n, 0, n)
    assert result["significant"] is False
    assert "Not enough engagement" in result["verdict"]


def test_the_refusal_says_how_many_are_needed():
    """An admin reading it should learn what would make the test possible,
    not just that it failed."""
    result = ab_verdict(1, 5, 1, 5)
    assert str(MIN_GROUP_FOR_SIGNIFICANCE) in result["verdict"]


# --- the verdicts -------------------------------------------------------------


def test_a_real_difference_names_the_better_variant():
    result = ab_verdict(60, 100, 40, 100)
    assert result["significant"] is True
    assert "Variant A" in result["verdict"]


def test_the_better_variant_is_identified_correctly_either_way():
    result = ab_verdict(40, 100, 60, 100)
    assert result["significant"] is True
    assert "Variant B" in result["verdict"]


def test_no_difference_is_stated_in_plain_language():
    """"No real difference" beats "p = 0.42" for the person reading it, and
    the number is still there for anyone who wants it."""
    result = ab_verdict(11, 120, 9, 120)
    assert result["significant"] is False
    assert "No real difference" in result["verdict"]
    assert result["p_value"] is not None


def test_a_verdict_never_claims_a_winner_it_cannot_support():
    """The property that matters: nothing below the threshold may produce a
    sentence naming a variant as better."""
    for x1, n1, x2, n2 in [
        (11, 120, 9, 120), (5, 40, 4, 40), (30, 200, 34, 200),
    ]:
        result = ab_verdict(x1, n1, x2, n2)
        if not result["significant"]:
            assert "Variant A really" not in result["verdict"]
            assert "Variant B really" not in result["verdict"]


def test_engagement_minimum_is_lower_than_the_group_minimum():
    """Sanity check on the two guards: requiring more events than recipients
    would make the test unreachable."""
    assert MIN_EVENTS_FOR_SIGNIFICANCE < MIN_GROUP_FOR_SIGNIFICANCE
