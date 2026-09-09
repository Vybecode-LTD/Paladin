"""Regression tests for SMTP connection-mode selection.

Bug (2026-09-09, dev server): the admin Settings "use TLS" switch was passed
straight to aiosmtplib's ``start_tls`` (STARTTLS). Port 465 requires implicit
TLS (``use_tls``), so any 465 configuration opened a plaintext connection,
waited 30 s for a greeting that never came, and surfaced as a Gateway Time-out
from the front proxy. These tests pin the mapping so it cannot regress.
"""
import pytest

from app.services.email_service import (
    DEMO_REPLY_FROM,
    SMTP_TIMEOUT_SECONDS,
    resolve_from_email,
    smtp_tls_options,
)


# --- sender address -----------------------------------------------------------
# The From address is admin-configurable since 2026-09-09; an empty value keeps
# the historical default so existing rows behave exactly as before.

@pytest.mark.parametrize("configured", ["", "   ", None])
def test_empty_or_missing_sender_falls_back_to_default(configured):
    assert resolve_from_email(configured) == DEMO_REPLY_FROM


def test_configured_sender_is_used_verbatim_but_trimmed():
    assert resolve_from_email("info@basefra.me") == "info@basefra.me"
    assert resolve_from_email("  info@basefra.me  ") == "info@basefra.me"


def test_default_sender_is_the_ashford_briggs_info_address():
    assert DEMO_REPLY_FROM == "info@ashfordbriggs.com"


# --- TLS mode -----------------------------------------------------------------


def test_port_465_always_uses_implicit_tls_regardless_of_switch():
    for switch in (True, False):
        opts = smtp_tls_options(465, switch)
        assert opts == {"use_tls": True, "start_tls": False}


def test_port_587_with_switch_on_uses_starttls():
    assert smtp_tls_options(587, True) == {"use_tls": False, "start_tls": True}


def test_port_587_with_switch_off_is_plain():
    assert smtp_tls_options(587, False) == {"use_tls": False, "start_tls": False}


def test_other_ports_follow_the_switch():
    assert smtp_tls_options(2525, True) == {"use_tls": False, "start_tls": True}
    assert smtp_tls_options(25, False) == {"use_tls": False, "start_tls": False}


def test_options_are_never_both_tls_modes():
    """aiosmtplib raises ValueError if use_tls and start_tls are both set."""
    for port in (25, 465, 587, 2525):
        for switch in (True, False):
            opts = smtp_tls_options(port, switch)
            assert not (opts["use_tls"] and opts["start_tls"])


def test_timeout_is_shorter_than_a_typical_proxy_timeout():
    """The send must fail with a real error before the front proxy's ~30 s
    limit, otherwise the admin sees an opaque 504 instead of the message."""
    assert 0 < SMTP_TIMEOUT_SECONDS <= 20
