"""Tests for mapping Mailgun events onto our own event types and tiers.

The split that matters most is `failed`. Mailgun reports a dead mailbox and a
temporarily full one under the same event name, distinguished only by
`severity`. Treating them alike either suppresses live contacts on a transient
error, or keeps mailing addresses that will never accept mail again — and a
rising hard-bounce rate is one of the fastest ways to lose domain reputation.
"""
from datetime import datetime, timezone

import pytest

from app.models.email_event import EventTier, EventType
from app.models.suppression import SuppressionReason
from app.services.event_service import (
    SUPPRESSING_EVENTS, classify_mailgun, occurred_at_of,
    provider_message_id_of, recipient_of, token_of,
)


# --- failed splits on severity ------------------------------------------------


def test_permanent_failure_is_a_hard_bounce():
    assert classify_mailgun({"event": "failed", "severity": "permanent"}) == \
        (EventType.hard_bounced, EventTier.exact)


def test_temporary_failure_is_a_soft_bounce():
    assert classify_mailgun({"event": "failed", "severity": "temporary"}) == \
        (EventType.soft_bounced, EventTier.exact)


def test_failure_with_no_severity_is_treated_as_soft():
    """The safer default: a soft bounce does not suppress, so an unexpected
    payload shape cannot silently retire a live contact."""
    assert classify_mailgun({"event": "failed"}) == \
        (EventType.soft_bounced, EventTier.exact)


def test_only_hard_bounces_suppress():
    assert EventType.hard_bounced in SUPPRESSING_EVENTS
    assert EventType.soft_bounced not in SUPPRESSING_EVENTS


# --- the rest of the mapping ---------------------------------------------------


@pytest.mark.parametrize(
    "name,expected",
    [
        ("accepted", EventType.accepted),
        ("delivered", EventType.delivered),
        ("complained", EventType.complained),
        ("unsubscribed", EventType.unsubscribed),
    ],
)
def test_provider_facts_are_exact_tier(name, expected):
    """These are statements by the mail system about what it did. Nothing is
    being inferred, so they carry the highest tier."""
    event_type, tier = classify_mailgun({"event": name})
    assert event_type == expected
    assert tier == EventTier.exact


@pytest.mark.parametrize("name", ["opened", "clicked"])
def test_provider_engagement_is_only_ever_inferred(name):
    """We disable Mailgun's own tracking on every send, so these should never
    arrive. If a domain-level setting re-enables them, they must still land as
    inferred — around half of all tracked opens industry-wide are automatic
    prefetch, and recording them as fact is the exact dishonesty this system
    exists to avoid."""
    _, tier = classify_mailgun({"event": name})
    assert tier == EventTier.inferred


def test_event_names_are_case_insensitive():
    assert classify_mailgun({"event": "DELIVERED"})[0] == EventType.delivered


def test_unknown_event_is_ignored_rather_than_guessed():
    assert classify_mailgun({"event": "some_future_event"}) is None
    assert classify_mailgun({}) is None


def test_complaint_and_unsubscribe_both_suppress_with_distinct_reasons():
    """Both stop the mail, but the reason is kept because a complaint is a
    reputation event and an unsubscribe is a preference."""
    assert SUPPRESSING_EVENTS[EventType.complained] == SuppressionReason.complained
    assert SUPPRESSING_EVENTS[EventType.unsubscribed] == SuppressionReason.unsubscribed


# --- field extraction ----------------------------------------------------------


def test_timestamp_is_parsed_from_float_epoch():
    at = occurred_at_of({"timestamp": 1770919267.4288595})
    assert at.tzinfo is timezone.utc
    assert at.year == 2026


@pytest.mark.parametrize("bad", [None, "", "not-a-number", {}])
def test_malformed_timestamp_falls_back_to_now(bad):
    """An event with a broken timestamp is still a real event; discarding it
    would lose a suppression."""
    before = datetime.now(timezone.utc)
    at = occurred_at_of({"timestamp": bad})
    assert at >= before


def test_recipient_is_normalised_to_match_the_suppression_list():
    """Mailgun echoes the address as it was sent. If a campaign was sent to a
    mixed-case address, the complaint arrives mixed-case, and an un-normalised
    write would create a suppression that later lookups miss."""
    assert recipient_of({"recipient": "  Bob@Example.COM "}) == "bob@example.com"


def test_missing_recipient_is_empty_not_an_error():
    assert recipient_of({}) == ""


def test_token_is_read_from_user_variables():
    """The custom variable we attach on the way out is the primary way an
    event finds its message."""
    assert token_of({"user-variables": {"message_token": "abc123"}}) == "abc123"


def test_token_handles_mailgun_sending_an_empty_list():
    """Mailgun serialises absent user variables as [] rather than {}, which is
    what the real payloads in their docs show."""
    assert token_of({"user-variables": []}) == ""
    assert token_of({}) == ""


def test_provider_message_id_is_read_from_headers():
    event = {"message": {"headers": {"message-id": "2026@mg.example.com"}}}
    assert provider_message_id_of(event) == "2026@mg.example.com"


def test_provider_message_id_missing_is_empty():
    assert provider_message_id_of({}) == ""
    assert provider_message_id_of({"message": {}}) == ""
    assert provider_message_id_of({"message": {"headers": {}}}) == ""
