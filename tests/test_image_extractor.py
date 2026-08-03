from __future__ import annotations

from feedparser import FeedParserDict

from scripts.image_extractor import extract_rss_image


def test_image_priority_and_scheme_validation() -> None:
    entry = FeedParserDict(
        media_thumbnail=[{"url": "javascript:bad"}],
        media_content=[{"url": "https://example.com/media.jpg", "type": "image/jpeg"}],
        enclosures=[{"href": "https://example.com/enclosure.jpg", "type": "image/jpeg"}],
        summary='<img src="https://example.com/summary.jpg">',
    )

    image, _license = extract_rss_image(entry)
    assert image == "https://example.com/media.jpg"


def test_summary_image_is_last_rss_only_fallback() -> None:
    entry = FeedParserDict(summary='<p>x</p><img src="http://example.com/summary.jpg">')
    image, _license = extract_rss_image(entry)
    assert image == "http://example.com/summary.jpg"
