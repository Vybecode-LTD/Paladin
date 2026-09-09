"""Regression tests for address normalisation in the send guard.

The failure this prevents: suppression is stored for "bob@example.com" and a
later campaign imports "Bob@Example.com". Without normalisation on both the
write and the read, the lookup misses and a person who pressed the spam
button, or asked to stop, is mailed again. That is the single worst bug this
system could ship — it is a legal problem, and complaints are the heaviest
negative signal a mailbox provider weighs.
"""
from app.services.suppression_service import normalize


def test_case_is_folded():
    assert normalize("Bob@Example.COM") == "bob@example.com"


def test_surrounding_whitespace_is_stripped():
    """Pasted from a spreadsheet, an address routinely arrives with a stray
    space or newline attached."""
    assert normalize("  bob@example.com\n") == "bob@example.com"
    assert normalize("\tbob@example.com ") == "bob@example.com"


def test_case_and_whitespace_together():
    assert normalize("  BOB@Example.Com  ") == "bob@example.com"


def test_empty_and_none_are_safe():
    """Called on whatever a webhook or an import row supplies, which is not
    always a string. Returning "" keeps the guard a miss rather than raising
    inside a send loop."""
    assert normalize("") == ""
    assert normalize(None) == ""


def test_already_normalized_is_unchanged():
    assert normalize("bob@example.com") == "bob@example.com"


def test_normalize_is_idempotent():
    once = normalize("  Bob@Example.com ")
    assert normalize(once) == once


def test_internal_case_of_local_part_is_also_folded():
    """Strictly, the local part may be case-sensitive per RFC 5321, but no
    mail provider in practice treats it that way, and every major one folds
    it. Matching that behaviour is what keeps a suppression effective; the
    opposite choice would let "Bob@" slip past a suppression on "bob@"."""
    assert normalize("BoB.HatHcoat@Example.com") == "bob.hathcoat@example.com"
