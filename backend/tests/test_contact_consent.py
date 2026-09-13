"""Tests for the consent rules on Contact.

These two properties decide whether a person is mailed at all, and whether a
tracking pixel is embedded for them. Getting either wrong is a legal problem
rather than a cosmetic one: Canada requires consent before the first send, and
April 2026 guidance from the French and Italian regulators treats per-recipient
open tracking as needing its own consent, separate from consent to receive the
mail.
"""
import pytest

from app.models.campaign_message import new_tracking_token
from app.models.contact import ConsentBasis, Contact, ContactStatus


def _contact(**overrides) -> Contact:
    """Constructed in memory, never persisted — these are pure rules and must
    stay testable without a database."""
    defaults = {
        "email": "bob@example.com",
        "status": ContactStatus.active,
        "consent_basis": ConsentBasis.express,
        "country": "US",
        "tracking_consent": False,
    }
    return Contact(**{**defaults, **overrides})


# --- who may be mailed --------------------------------------------------------


def test_active_contact_with_a_basis_is_mailable():
    assert _contact().is_mailable


@pytest.mark.parametrize(
    "status",
    [ContactStatus.unsubscribed, ContactStatus.bounced, ContactStatus.retired],
)
def test_only_active_contacts_are_mailable(status):
    assert not _contact(status=status).is_mailable


def test_unknown_consent_basis_is_never_mailable():
    """The default for an imported row. Making "no basis recorded" an explicit
    value rather than a null is what lets the guard refuse it."""
    assert not _contact(consent_basis=ConsentBasis.unknown).is_mailable


@pytest.mark.parametrize(
    "basis",
    [
        ConsentBasis.express,
        ConsentBasis.implied,
        ConsentBasis.contract,
        ConsentBasis.signup,
        ConsentBasis.demo_request,
    ],
)
def test_every_real_basis_is_mailable(basis):
    assert _contact(consent_basis=basis).is_mailable


def test_a_basis_does_not_override_an_unsubscribe():
    """The combination that matters: someone who once signed up and has since
    unsubscribed. Consent recorded in the past must not resurrect them."""
    contact = _contact(consent_basis=ConsentBasis.express, status=ContactStatus.unsubscribed)
    assert not contact.is_mailable


# --- who may be tracked -------------------------------------------------------


def test_us_contacts_may_be_tracked_without_separate_consent():
    assert _contact(country="US", tracking_consent=False).may_track_opens


def test_country_code_case_does_not_matter():
    """Imported data arrives in whatever case the source used."""
    assert _contact(country="us").may_track_opens


@pytest.mark.parametrize("country", ["CA", "GB", "FR", "IE", "DE"])
def test_non_us_contacts_need_explicit_tracking_consent(country):
    assert not _contact(country=country, tracking_consent=False).may_track_opens
    assert _contact(country=country, tracking_consent=True).may_track_opens


def test_unknown_country_is_treated_as_the_stricter_rule():
    """An imported row with no country must not silently get the US
    treatment — defaulting the permissive way is how a European contact ends
    up tracked without consent."""
    assert not _contact(country="", tracking_consent=False).may_track_opens


def test_explicit_consent_works_regardless_of_country():
    assert _contact(country="", tracking_consent=True).may_track_opens


def test_tracking_consent_is_independent_of_mailability():
    """A contact can be perfectly mailable and still not trackable. The two
    questions are separate, which is the whole point of the second field."""
    contact = _contact(country="DE", consent_basis=ConsentBasis.express, tracking_consent=False)
    assert contact.is_mailable
    assert not contact.may_track_opens


# --- tracking tokens ----------------------------------------------------------


def test_tokens_are_unique_across_many_draws():
    assert len({new_tracking_token() for _ in range(2000)}) == 2000


def test_tokens_are_url_safe():
    """They go in a URL inside sent mail; a token needing escaping would break
    the link in some clients."""
    allowed = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_")
    for _ in range(200):
        assert set(new_tracking_token()) <= allowed


def test_tokens_carry_enough_entropy_to_be_unguessable():
    """A guessable token would let anyone forge an open, a click or an
    unsubscribe for someone else's message. 16 random bytes is 22 characters
    once base64url-encoded."""
    token = new_tracking_token()
    assert len(token) >= 22
