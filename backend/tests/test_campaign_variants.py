"""Tests for holdout and A/B assignment.

The property that matters is determinism. A send that crashes half way is
resumed by re-expanding the campaign, and if assignment were random the second
pass would reshuffle everyone — destroying the holdout the campaign is
measured against and putting some contacts in both variants across retries.
"""
import uuid

import pytest

from app.models.campaign import Campaign
from app.models.contact import Contact
from app.services.campaign_service import (
    HOLDOUT, assign_variant, subject_for,
)

CAMPAIGN_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")


def _campaign(**overrides) -> Campaign:
    defaults = {
        "name": "Deployment update",
        "subject": "Paladin is live",
        "holdout_percent": 0,
        "variant_b_subject": "",
    }
    campaign = Campaign(**{**defaults, **overrides})
    campaign.id = CAMPAIGN_ID
    return campaign


def _contacts(n: int) -> list[Contact]:
    """Stable ids, so a failure is reproducible rather than a different random
    sample every run."""
    out = []
    for i in range(n):
        contact = Contact(email=f"person{i}@example.com")
        contact.id = uuid.UUID(int=i, version=4)
        out.append(contact)
    return out


# --- determinism --------------------------------------------------------------


def test_assignment_is_stable_across_calls():
    campaign = _campaign(holdout_percent=20, variant_b_subject="Other subject")
    for contact in _contacts(50):
        first = assign_variant(campaign, contact)
        assert all(assign_variant(campaign, contact) == first for _ in range(5))


def test_different_campaigns_assign_independently():
    """Otherwise the same people land in the holdout every single campaign and
    are never mailed at all."""
    a = _campaign(holdout_percent=30)
    b = _campaign(holdout_percent=30)
    b.id = uuid.UUID("22222222-2222-2222-2222-222222222222")

    contacts = _contacts(300)
    holdout_a = {c.id for c in contacts if assign_variant(a, c) == HOLDOUT}
    holdout_b = {c.id for c in contacts if assign_variant(b, c) == HOLDOUT}
    assert holdout_a != holdout_b
    # Some overlap is expected by chance; near-total overlap would mean the
    # campaign id is not really participating.
    overlap = len(holdout_a & holdout_b) / max(len(holdout_a), 1)
    assert overlap < 0.75


# --- holdout ------------------------------------------------------------------


def test_zero_holdout_holds_nobody_back():
    campaign = _campaign(holdout_percent=0)
    assert all(assign_variant(campaign, c) != HOLDOUT for c in _contacts(200))


@pytest.mark.parametrize("percent", [10, 25, 50])
def test_holdout_size_is_close_to_the_requested_percentage(percent):
    campaign = _campaign(holdout_percent=percent)
    contacts = _contacts(2000)
    held = sum(1 for c in contacts if assign_variant(campaign, c) == HOLDOUT)
    ratio = held / len(contacts)
    assert abs(ratio - percent / 100) < 0.05


def test_holdout_percent_is_clamped_not_trusted():
    """Schema validation caps this at 50, but the function is also called from
    the worker against whatever is in the database, which a migration or a
    manual edit could have put out of range."""
    campaign = _campaign(holdout_percent=500)
    assert all(assign_variant(campaign, c) == HOLDOUT for c in _contacts(50))

    campaign = _campaign(holdout_percent=-10)
    assert all(assign_variant(campaign, c) != HOLDOUT for c in _contacts(50))


# --- A/B ----------------------------------------------------------------------


def test_without_a_b_subject_everyone_is_variant_a():
    campaign = _campaign(variant_b_subject="")
    assert {assign_variant(campaign, c) for c in _contacts(200)} == {"a"}


def test_whitespace_only_b_subject_is_not_an_a_b_test():
    """An author who clears the field leaves a space behind more often than
    not; treating that as a live test would split the list for no reason."""
    campaign = _campaign(variant_b_subject="   ")
    assert {assign_variant(campaign, c) for c in _contacts(100)} == {"a"}


def test_a_b_split_is_roughly_even():
    campaign = _campaign(variant_b_subject="A different subject")
    variants = [assign_variant(campaign, c) for c in _contacts(2000)]
    a, b = variants.count("a"), variants.count("b")
    assert abs(a - b) / len(variants) < 0.06


def test_holdout_and_variant_are_independent():
    """Both derive from a hash of the same two ids, so they must be salted
    differently. Sharing one hash would make variant B systematically
    over-represent contacts near the holdout boundary, quietly biasing every
    A/B result the dashboard reports."""
    campaign = _campaign(holdout_percent=50, variant_b_subject="B")
    variants = [
        assign_variant(campaign, c)
        for c in _contacts(2000)
    ]
    sent = [v for v in variants if v != HOLDOUT]
    a, b = sent.count("a"), sent.count("b")
    assert abs(a - b) / max(len(sent), 1) < 0.08


# --- subject selection --------------------------------------------------------


def test_variant_b_gets_the_b_subject():
    campaign = _campaign(variant_b_subject="Second subject")
    assert subject_for(campaign, "b") == "Second subject"
    assert subject_for(campaign, "a") == "Paladin is live"


def test_variant_b_falls_back_when_no_b_subject_exists():
    """Defensive: a campaign edited to clear the B subject after expansion
    still has messages marked variant b, and they must not go out blank."""
    campaign = _campaign(variant_b_subject="")
    assert subject_for(campaign, "b") == "Paladin is live"
