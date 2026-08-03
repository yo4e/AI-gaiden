from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

import feedparser
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from scripts.image_extractor import extract_rss_image
from scripts.models import FeedConfig, NormalizedItem
from scripts.utils import (
    is_http_url,
    load_json,
    make_dedupe_key,
    normalize_url,
    parse_feed_datetime,
    sanitize_html,
    write_json_atomic,
)

LOGGER = logging.getLogger(__name__)
USER_AGENT = "AI-Gaiden/0.1 (+https://github.com/yo4e/AI-gaiden)"
ACCEPTED_CONTENT_TYPES = ("xml", "rss", "atom")
MAX_FEED_BYTES = 10 * 1024 * 1024


class FeedParseError(ValueError):
    """Raised when a feed cannot be safely parsed into any entries."""


@dataclass(frozen=True, slots=True)
class FeedResult:
    config: FeedConfig
    success: bool
    not_modified: bool
    items: tuple[NormalizedItem, ...]
    error: str | None = None


def parse_feed_bytes(payload: bytes, config: FeedConfig) -> list[NormalizedItem]:
    if len(payload) > MAX_FEED_BYTES:
        raise FeedParseError(f"Feed exceeds {MAX_FEED_BYTES} bytes")
    parsed = feedparser.parse(payload)
    if parsed.bozo and not parsed.entries:
        raise FeedParseError(f"Malformed feed: {parsed.bozo_exception}")
    if parsed.bozo:
        LOGGER.warning("Feed %s was parsed with a warning: %s", config.id, parsed.bozo_exception)

    items: list[NormalizedItem] = []
    for entry in parsed.entries[: config.max_items_per_run]:
        normalized = normalize_entry(entry, config)
        if normalized:
            items.append(normalized)
    if parsed.bozo and not items:
        raise FeedParseError(f"Malformed feed produced no usable entries: {parsed.bozo_exception}")
    return items


def normalize_entry(entry: Any, config: FeedConfig) -> NormalizedItem | None:
    title = sanitize_html(entry.get("title"))
    if not title:
        return None
    guid_value = entry.get("id") or entry.get("guid")
    guid = sanitize_html(str(guid_value)) if guid_value else None
    link_value = str(entry.get("link") or "").strip()
    if not is_http_url(link_value) and guid and is_http_url(guid):
        link_value = guid
    canonical_url = normalize_url(link_value)
    if not canonical_url:
        return None

    raw_date = entry.get("published") or entry.get("updated")
    published_at = parse_feed_datetime(str(raw_date)) if raw_date else None
    date_status = "known" if published_at else "unknown"
    summary_html = entry.get("summary") or entry.get("description") or ""
    summary = sanitize_html(str(summary_html))
    author_value = entry.get("author")
    author = sanitize_html(str(author_value)) if author_value else None
    image_url, image_license = extract_rss_image(entry)
    dedupe_key = (
        make_dedupe_key(
            canonical_url=canonical_url,
            guid=guid,
            source_id=config.id,
            title=title,
            published_at=published_at,
        )
        if published_at
        else ""
    )
    return NormalizedItem(
        source_id=config.id,
        source_name=config.name,
        title=title,
        url=link_value,
        canonical_url=canonical_url,
        guid=guid,
        published_at=published_at,
        date_status=date_status,
        summary=summary,
        author=author,
        image_url=image_url,
        image_license=image_license,
        dedupe_key=dedupe_key,
    )


class FeedReader:
    def __init__(self, cache_path: Path) -> None:
        self.cache_path = cache_path
        self.use_conditional_requests = True
        self.cache = load_json(cache_path, {"feeds": {}})
        if not isinstance(self.cache.get("feeds"), dict):
            self.cache = {"feeds": {}}
        retry = Retry(
            total=2,
            connect=2,
            read=2,
            status=2,
            backoff_factor=0.8,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=frozenset({"GET"}),
            respect_retry_after_header=True,
        )
        self.session = requests.Session()
        self.session.mount("http://", HTTPAdapter(max_retries=retry))
        self.session.mount("https://", HTTPAdapter(max_retries=retry))

    def fetch_all(self, configs: list[FeedConfig]) -> list[FeedResult]:
        results: list[FeedResult] = []
        visited_hosts: set[str] = set()
        cache_changed = False
        for config in configs:
            if not config.enabled:
                continue
            host = (urlsplit(config.url).hostname or "").lower()
            if host in visited_hosts:
                results.append(
                    FeedResult(
                        config=config,
                        success=False,
                        not_modified=False,
                        items=(),
                        error=f"Host {host} was already requested during this run",
                    )
                )
                continue
            visited_hosts.add(host)
            result, changed = self._fetch(config)
            results.append(result)
            cache_changed = cache_changed or changed
        if cache_changed:
            write_json_atomic(self.cache_path, self.cache)
        return results

    def _fetch(self, config: FeedConfig) -> tuple[FeedResult, bool]:
        state = self.cache["feeds"].get(config.id, {})
        headers = {
            "User-Agent": USER_AGENT,
            "Accept": "application/atom+xml, application/rss+xml, application/xml, text/xml;q=0.9",
        }
        if self.use_conditional_requests and state.get("etag"):
            headers["If-None-Match"] = state["etag"]
        if self.use_conditional_requests and state.get("last_modified"):
            headers["If-Modified-Since"] = state["last_modified"]
        try:
            response = self.session.get(
                config.url,
                headers=headers,
                timeout=(10, 30),
                allow_redirects=True,
            )
            if response.status_code == 304:
                return FeedResult(config, True, True, ()), False
            response.raise_for_status()
            content_type = response.headers.get("Content-Type", "").lower()
            if not any(marker in content_type for marker in ACCEPTED_CONTENT_TYPES):
                raise FeedParseError(f"Unexpected Content-Type: {content_type or 'missing'}")
            items = parse_feed_bytes(response.content, config)
        except (requests.RequestException, FeedParseError) as exc:
            return FeedResult(config, False, False, (), str(exc)), False

        new_state = {
            "etag": response.headers.get("ETag"),
            "last_modified": response.headers.get("Last-Modified"),
            "resolved_url": response.url,
        }
        new_state = {key: value for key, value in new_state.items() if value}
        changed = state != new_state
        self.cache["feeds"][config.id] = new_state
        return FeedResult(config, True, False, tuple(items)), changed
