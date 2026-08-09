from __future__ import annotations

from datetime import UTC

import pytest
import requests

from scripts.feed_reader import FeedParseError, FeedReader, parse_feed_bytes
from scripts.models import FeedConfig


def test_parses_rss_sanitizes_html_and_uses_image_priority(
    fixture_dir, feed_config: FeedConfig
) -> None:
    items = parse_feed_bytes((fixture_dir / "rss.xml").read_bytes(), feed_config)

    assert len(items) == 2
    first = items[0]
    assert first.title == "Example Model v2.1 is available"
    assert "alert" not in first.summary
    assert "introduced a model" in first.summary
    assert first.canonical_url == "https://example.com/news/model?keep=yes"
    assert first.image_url == "https://cdn.example.com/thumb.jpg"
    assert first.published_at is not None
    assert first.published_at.tzinfo == UTC
    assert first.date_status == "known"


def test_uses_permalink_guid_when_link_is_missing(fixture_dir, feed_config: FeedConfig) -> None:
    items = parse_feed_bytes((fixture_dir / "rss.xml").read_bytes(), feed_config)

    assert items[1].url == "https://example.com/news/guid-only"
    assert items[1].canonical_url == "https://example.com/news/guid-only"


def test_parses_atom_and_updated_date(fixture_dir, feed_config: FeedConfig) -> None:
    items = parse_feed_bytes((fixture_dir / "atom.xml").read_bytes(), feed_config)

    assert len(items) == 1
    assert items[0].title == "Research toolkit update"
    assert items[0].canonical_url == "https://atom.example.com/posts/toolkit"
    assert items[0].author == "Example Labs"
    assert items[0].image_url == "https://cdn.atom.example.com/toolkit.png"


def test_rejects_malformed_feed(fixture_dir, feed_config: FeedConfig) -> None:
    with pytest.raises(FeedParseError):
        parse_feed_bytes((fixture_dir / "malformed.xml").read_bytes(), feed_config)


def test_marks_missing_date_unknown(feed_config: FeedConfig) -> None:
    payload = b"""<?xml version='1.0'?><rss version='2.0'><channel><title>x</title>
    <item><title>No date</title><link>https://example.com/no-date</link></item>
    </channel></rss>"""

    item = parse_feed_bytes(payload, feed_config)[0]
    assert item.date_status == "unknown"
    assert item.published_at is None
    assert item.dedupe_key == ""


def test_fetch_accepts_feed_xml_served_as_text_plain(
    tmp_path, fixture_dir, feed_config: FeedConfig, monkeypatch
) -> None:
    response = requests.Response()
    response.status_code = 200
    response._content = (fixture_dir / "rss.xml").read_bytes()
    response.headers["Content-Type"] = "text/plain; charset=utf-8"
    response.url = feed_config.url

    reader = FeedReader(tmp_path / "feed-state.json")
    monkeypatch.setattr(reader.session, "get", lambda *args, **kwargs: response)

    result, _ = reader._fetch(feed_config)

    assert result.success is True
    assert len(result.items) == 2


def test_fetch_rejects_html_with_non_feed_content_type(
    tmp_path, feed_config: FeedConfig, monkeypatch
) -> None:
    response = requests.Response()
    response.status_code = 200
    response._content = b"<!doctype html><html><body>not a feed</body></html>"
    response.headers["Content-Type"] = "text/html; charset=utf-8"
    response.url = feed_config.url

    reader = FeedReader(tmp_path / "feed-state.json")
    monkeypatch.setattr(reader.session, "get", lambda *args, **kwargs: response)

    result, _ = reader._fetch(feed_config)

    assert result.success is False
    assert result.error == "Unexpected Content-Type: text/html; charset=utf-8"
