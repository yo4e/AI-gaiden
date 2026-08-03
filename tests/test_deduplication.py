from __future__ import annotations

from datetime import UTC, datetime

from scripts.utils import make_dedupe_key, normalize_url


def test_normalize_url_removes_fragment_tracking_and_default_port() -> None:
    value = "https://EXAMPLE.com:443/path/?utm_source=rss&keep=1&ref=x#fragment"
    assert normalize_url(value) == "https://example.com/path?keep=1"


def test_normalize_url_does_not_rewrite_http_to_https() -> None:
    assert normalize_url("http://Example.com/news/") == "http://example.com/news"


def test_normalize_url_rejects_malformed_or_whitespace_urls() -> None:
    assert normalize_url("https://example.com:bad/path") == ""
    assert normalize_url("https://example.com/bad path") == ""


def test_canonical_url_has_priority_over_guid() -> None:
    published = datetime(2026, 8, 3, tzinfo=UTC)
    first = make_dedupe_key(
        canonical_url="https://example.com/post",
        guid="first-guid",
        source_id="source",
        title="Title",
        published_at=published,
    )
    second = make_dedupe_key(
        canonical_url="https://example.com/post",
        guid="different-guid",
        source_id="source",
        title="Different title",
        published_at=published,
    )
    assert first == second


def test_fallback_key_uses_source_title_and_date() -> None:
    published = datetime(2026, 8, 3, tzinfo=UTC)
    first = make_dedupe_key(
        canonical_url="",
        guid=None,
        source_id="source-a",
        title="  Same   TITLE ",
        published_at=published,
    )
    second = make_dedupe_key(
        canonical_url="",
        guid=None,
        source_id="source-a",
        title="same title",
        published_at=published,
    )
    assert first == second
