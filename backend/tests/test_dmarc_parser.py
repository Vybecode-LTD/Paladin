"""Tests for the DMARC aggregate report parser.

These reports are the only complete answer to "what sends as our domain", and
that answer is the gate on tightening the domain policy. Misreading one means
either enforcing while a legitimate sender still fails — which silently stops
the company's own mail — or never enforcing at all because a forwarder looks
like a failure forever.
"""
import gzip
import io
import zipfile
from datetime import date

import pytest

from app.services.dmarc_service import DmarcParseError, decompress, parse

REPORT = """<?xml version="1.0" encoding="UTF-8" ?>
<feedback>
  <report_metadata>
    <org_name>google.com</org_name>
    <email>noreply-dmarc-support@google.com</email>
    <report_id>1234567890</report_id>
    <date_range><begin>1788652800</begin><end>1788739199</end></date_range>
  </report_metadata>
  <policy_published>
    <domain>ashfordbriggs.com</domain>
    <adkim>r</adkim><aspf>r</aspf>
    <p>none</p><sp>none</sp><pct>100</pct>
  </policy_published>
  <record>
    <row>
      <source_ip>209.85.220.41</source_ip>
      <count>12</count>
      <policy_evaluated><disposition>none</disposition><dkim>pass</dkim><spf>pass</spf></policy_evaluated>
    </row>
    <identifiers><header_from>ashfordbriggs.com</header_from></identifiers>
    <auth_results>
      <dkim><domain>ashfordbriggs.com</domain><result>pass</result></dkim>
      <spf><domain>ashfordbriggs.com</domain><result>pass</result></spf>
    </auth_results>
  </record>
  <record>
    <row>
      <source_ip>198.51.100.7</source_ip>
      <count>3</count>
      <policy_evaluated><disposition>none</disposition><dkim>fail</dkim><spf>fail</spf></policy_evaluated>
    </row>
    <identifiers><header_from>ashfordbriggs.com</header_from></identifiers>
    <auth_results>
      <dkim><domain>someoneelse.example</domain><result>pass</result></dkim>
      <spf><domain>someoneelse.example</domain><result>pass</result></spf>
    </auth_results>
  </record>
</feedback>
"""


def test_a_whole_report_parses():
    records = parse(REPORT.encode())
    assert len(records) == 2


def test_metadata_is_carried_onto_every_record():
    for r in parse(REPORT.encode()):
        assert r.org_name == "google.com"
        assert r.report_id == "1234567890"
        assert r.policy_domain == "ashfordbriggs.com"
        assert r.policy_p == "none"


def test_date_range_is_converted_from_epoch_in_utc():
    """Reports carry epoch seconds and cover one UTC day. Asserted on
    properties rather than a hand-computed calendar date, because getting the
    expectation wrong by a day proves nothing about the parser — which is
    exactly what happened when this test was first written."""
    r = parse(REPORT.encode())[0]
    assert isinstance(r.date_begin, date) and isinstance(r.date_end, date)
    assert r.date_begin <= r.date_end
    # The window in the fixture is one day less a second, so it must not span
    # more than a single day boundary.
    assert (r.date_end - r.date_begin).days <= 1


def test_a_malformed_epoch_does_not_raise():
    """A report with a broken date is still worth its sending records."""
    xml = REPORT.replace("<begin>1788652800</begin>", "<begin>not-a-number</begin>")
    assert parse(xml.encode())[0].date_begin is not None


def test_a_passing_source_is_recorded_as_aligned():
    r = parse(REPORT.encode())[0]
    assert r.source_ip == "209.85.220.41"
    assert r.count == 12
    assert r.dkim_aligned and r.spf_aligned


def test_alignment_comes_from_policy_evaluated_not_the_raw_auth_results():
    """The second record is the case that matters. Its raw DKIM and SPF both
    say "pass" — but for someoneelse.example, not for us. That is a forged
    From address, and reading the raw results instead of policy_evaluated
    would report it as a healthy sender."""
    r = parse(REPORT.encode())[1]
    assert r.dkim_aligned is False
    assert r.spf_aligned is False
    assert r.dkim_domain == "someoneelse.example"


def test_a_passing_dkim_signature_wins_over_a_failing_one():
    """A forwarded message carries the forwarder's signature as well as ours.
    Taking the first one listed would report our own mail as unsigned."""
    xml = REPORT.replace(
        "<dkim><domain>ashfordbriggs.com</domain><result>pass</result></dkim>",
        "<dkim><domain>forwarder.example</domain><result>fail</result></dkim>"
        "<dkim><domain>ashfordbriggs.com</domain><result>pass</result></dkim>",
    )
    assert parse(xml.encode())[0].dkim_domain == "ashfordbriggs.com"


# --- compression --------------------------------------------------------------


def test_gzipped_reports_are_read():
    assert parse(gzip.compress(REPORT.encode()))


def test_zipped_reports_are_read():
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("report.xml", REPORT)
    assert parse(buf.getvalue())


def test_bare_xml_is_read():
    assert parse(REPORT.encode())


def test_compression_is_detected_by_content_not_by_filename():
    """The filename comes from a mail attachment that providers do not agree
    on and that a client may have rewritten, so it cannot be trusted."""
    assert decompress(gzip.compress(b"hello")) == b"hello"
    assert decompress(b"hello") == b"hello"


def test_a_zip_with_no_xml_inside_is_an_error():
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("readme.txt", "nope")
    with pytest.raises(DmarcParseError):
        parse(buf.getvalue())


# --- bad input ----------------------------------------------------------------


def test_something_that_is_not_xml_is_rejected_clearly():
    with pytest.raises(DmarcParseError, match="Not valid XML"):
        parse(b"this is not xml at all")


def test_xml_that_is_not_a_dmarc_report_is_rejected():
    with pytest.raises(DmarcParseError, match="feedback"):
        parse(b"<html><body>an error page</body></html>")


def test_a_record_with_no_source_address_is_skipped_not_fatal():
    """Providers do occasionally emit a malformed row. Losing a whole day of
    visibility over one of them would be the wrong trade."""
    xml = REPORT.replace("<source_ip>198.51.100.7</source_ip>", "<source_ip></source_ip>")
    records = parse(xml.encode())
    assert len(records) == 1
    assert records[0].source_ip == "209.85.220.41"


def test_a_missing_count_defaults_to_zero_rather_than_raising():
    xml = REPORT.replace("<count>12</count>", "<count></count>")
    assert parse(xml.encode())[0].count == 0


def test_a_report_with_no_records_parses_to_an_empty_list():
    xml = REPORT[:REPORT.index("<record>")] + "</feedback>"
    assert parse(xml.encode()) == []
