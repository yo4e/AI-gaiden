from __future__ import annotations

import logging
import os
import re
from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from scripts.feed_reader import FeedResult
from scripts.models import FeedConfig, NormalizedItem
from scripts.utils import (
    load_json,
    make_dedupe_key,
    normalize_url,
    normalize_whitespace,
    parse_feed_datetime,
    sanitize_html,
    write_json_atomic,
)

LOGGER = logging.getLogger(__name__)
USER_AGENT = "AI-Gaiden/0.1 (+https://github.com/yo4e/AI-gaiden)"
GITHUB_API_VERSION = "2022-11-28"
MAX_RESPONSE_BYTES = 10 * 1024 * 1024
MARKDOWN_LINK_RE = re.compile(r"!?\[([^]]*)\]\([^)]*\)")
MARKDOWN_MARKER_RE = re.compile(r"(?:^|\s)(?:#{1,6}|[-*+]|\d+[.)])\s+")
MIN_UTC = datetime.min.replace(tzinfo=UTC)


def _plain_release_body(value: object) -> str:
    text = sanitize_html(str(value or ""))
    text = MARKDOWN_LINK_RE.sub(lambda match: match.group(1), text)
    text = MARKDOWN_MARKER_RE.sub(" ", text)
    return normalize_whitespace(text.replace("`", ""))


def normalize_release(payload: Mapping[str, Any], config: FeedConfig) -> NormalizedItem | None:
    if payload.get("draft") or payload.get("prerelease"):
        return None
    if not config.repository:
        return None

    tag = sanitize_html(str(payload.get("tag_name") or ""))
    title = sanitize_html(str(payload.get("name") or "")) or tag
    if not title:
        return None

    link_value = str(payload.get("html_url") or "").strip()
    canonical_url = normalize_url(link_value)
    if not canonical_url:
        return None
    parsed = urlsplit(canonical_url)
    expected_prefix = f"/{config.repository}/releases/"
    if parsed.hostname != "github.com" or not parsed.path.startswith(expected_prefix):
        LOGGER.warning("GitHub release URL is outside configured repository: %s", config.id)
        return None

    published_at = parse_feed_datetime(str(payload.get("published_at") or ""))
    if not published_at:
        return None

    release_id = payload.get("id")
    guid = f"github-release:{release_id}" if isinstance(release_id, int) else None
    author_data = payload.get("author")
    author = None
    if isinstance(author_data, Mapping):
        login = author_data.get("login")
        author = sanitize_html(str(login)) if login else None

    return NormalizedItem(
        source_id=config.id,
        source_name=config.name,
        title=title,
        url=link_value,
        canonical_url=canonical_url,
        guid=guid,
        published_at=published_at,
        date_status="known",
        summary=_plain_release_body(payload.get("body")),
        author=author,
        image_url=None,
        image_license=None,
        dedupe_key=make_dedupe_key(
            canonical_url=canonical_url,
            guid=guid,
            source_id=config.id,
            title=title,
            published_at=published_at,
        ),
        source_homepage=config.homepage,
    )


def normalize_release_list(payload: list[Any], config: FeedConfig) -> tuple[NormalizedItem, ...]:
    items = [
        item
        for release in payload
        if isinstance(release, Mapping)
        if (item := normalize_release(release, config)) is not None
    ]
    items.sort(key=lambda item: item.published_at or MIN_UTC, reverse=True)
    return tuple(items[: config.max_items_per_run])


class GitHubReleaseReader:
    """Fetch recent stable releases from explicitly configured official repositories."""

    def __init__(self, cache_path: Path) -> None:
        self.cache_path = cache_path
        self.use_conditional_requests = True
        self.cache = load_json(cache_path, {"sources": {}})
        if not isinstance(self.cache.get("sources"), dict):
            self.cache = {"sources": {}}
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
        self.session.mount("https://", HTTPAdapter(max_retries=retry))

    def fetch_all(self, configs: list[FeedConfig]) -> list[FeedResult]:
        results: list[FeedResult] = []
        cache_changed = False
        for config in configs:
            if not config.enabled or config.source_type != "github_releases":
                continue
            result, changed = self._fetch(config)
            results.append(result)
            cache_changed = cache_changed or changed
        if cache_changed:
            write_json_atomic(self.cache_path, self.cache)
        return results

    def _headers(self, state: Mapping[str, Any]) -> dict[str, str]:
        headers = {
            "User-Agent": USER_AGENT,
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": GITHUB_API_VERSION,
        }
        token = os.environ.get("GITHUB_TOKEN", "").strip()
        if token:
            headers["Authorization"] = f"Bearer {token}"
        if self.use_conditional_requests and state.get("etag"):
            headers["If-None-Match"] = str(state["etag"])
        return headers

    def _fetch(self, config: FeedConfig) -> tuple[FeedResult, bool]:
        state = self.cache["sources"].get(config.id, {})
        if not isinstance(state, dict):
            state = {}
        try:
            response = self.session.get(
                config.url,
                headers=self._headers(state),
                timeout=(10, 30),
                allow_redirects=False,
            )
            if response.status_code == 304:
                return FeedResult(config, True, True, ()), False
            if response.status_code == 403 and response.headers.get("X-RateLimit-Remaining") == "0":
                reset = response.headers.get("X-RateLimit-Reset", "unknown")
                raise requests.HTTPError(f"GitHub API rate limit exhausted; reset={reset}")
            response.raise_for_status()
            if len(response.content) > MAX_RESPONSE_BYTES:
                raise ValueError(f"GitHub API response exceeds {MAX_RESPONSE_BYTES} bytes")
            payload = response.json()
            if not isinstance(payload, list):
                raise ValueError("GitHub Releases API response must be a list")
            items = normalize_release_list(payload, config)
        except (requests.RequestException, requests.JSONDecodeError, ValueError) as exc:
            return FeedResult(config, False, False, (), str(exc)), False

        new_state = {"etag": response.headers.get("ETag"), "resolved_url": response.url}
        new_state = {key: value for key, value in new_state.items() if value}
        changed = state != new_state
        self.cache["sources"][config.id] = new_state
        return FeedResult(config, True, False, items), changed
