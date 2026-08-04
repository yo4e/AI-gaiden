from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import yaml
from bs4 import BeautifulSoup
from dateutil import parser as date_parser

from scripts.models import FeedConfig

TRACKING_PARAMETERS = {"ref", "source", "campaign"}
WHITESPACE_RE = re.compile(r"\s+")
FRONTMATTER_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*(?:\n|\Z)", re.DOTALL)


class ConfigurationError(ValueError):
    """Raised when a repository configuration file is unsafe or invalid."""


def sanitize_html(value: str | None) -> str:
    """Return plain text without executable or embedded feed markup."""
    if not value:
        return ""
    if "<" not in value and "&" not in value:
        return normalize_whitespace(value)
    soup = BeautifulSoup(value, "html.parser")
    for element in soup(["script", "style", "iframe", "object", "embed", "noscript"]):
        element.decompose()
    return normalize_whitespace(soup.get_text(" ", strip=True))


def normalize_whitespace(value: str) -> str:
    return WHITESPACE_RE.sub(" ", value).strip()


def is_http_url(value: str | None) -> bool:
    if not value:
        return False
    if any(character.isspace() or ord(character) < 32 for character in value):
        return False
    try:
        parsed = urlsplit(value.strip())
        # Accessing port validates malformed values such as ":not-a-port".
        _ = parsed.port
    except ValueError:
        return False
    return parsed.scheme.lower() in {"http", "https"} and bool(parsed.netloc)


def normalize_url(value: str) -> str:
    """Normalize a URL for deduplication without changing its transport scheme."""
    if not is_http_url(value):
        return ""
    parsed = urlsplit(value.strip())
    filtered_query = []
    for key, item_value in parse_qsl(parsed.query, keep_blank_values=True):
        lowered = key.lower()
        if lowered.startswith("utm_") or lowered in TRACKING_PARAMETERS:
            continue
        filtered_query.append((key, item_value))
    path = parsed.path
    if path != "/":
        path = path.rstrip("/")
    hostname = (parsed.hostname or "").lower()
    port = parsed.port
    default_port = (parsed.scheme.lower() == "http" and port == 80) or (
        parsed.scheme.lower() == "https" and port == 443
    )
    host = hostname if not port or default_port else f"{hostname}:{port}"
    if parsed.username or parsed.password:
        return ""
    return urlunsplit(
        (parsed.scheme.lower(), host, path or "/", urlencode(filtered_query, doseq=True), "")
    )


def parse_feed_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = date_parser.parse(value)
    except (TypeError, ValueError, OverflowError):
        return None
    if parsed.tzinfo is None:
        return None
    return parsed.astimezone(UTC)


def make_dedupe_key(
    *, canonical_url: str, guid: str | None, source_id: str, title: str, published_at: datetime
) -> str:
    if canonical_url:
        return f"url:{hashlib.sha256(canonical_url.encode()).hexdigest()}"
    if guid:
        return f"guid:{hashlib.sha256(guid.strip().encode()).hexdigest()}"
    normalized_title = normalize_whitespace(title).casefold()
    fallback = f"{source_id}\n{normalized_title}\n{published_at.date().isoformat()}"
    return f"fallback:{hashlib.sha256(fallback.encode()).hexdigest()}"


def load_feed_configs(path: Path) -> list[FeedConfig]:
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise ConfigurationError(f"Could not read feed configuration: {exc}") from exc
    if not isinstance(raw, dict) or not isinstance(raw.get("feeds"), list):
        raise ConfigurationError("Feed configuration must contain a feeds list")

    configs: list[FeedConfig] = []
    seen_ids: set[str] = set()
    for index, item in enumerate(raw["feeds"]):
        if not isinstance(item, dict):
            raise ConfigurationError(f"Feed at index {index} must be a mapping")
        required = {"id", "name", "url", "language", "enabled", "priority"}
        missing = required - item.keys()
        if missing:
            raise ConfigurationError(f"Feed at index {index} is missing: {sorted(missing)}")
        feed_id = str(item["id"])
        if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", feed_id) or feed_id in seen_ids:
            raise ConfigurationError(f"Feed id is invalid or duplicated: {feed_id}")
        if not is_http_url(str(item["url"])):
            raise ConfigurationError(f"Feed URL is not HTTP(S): {feed_id}")
        homepage = item.get("homepage")
        if homepage is not None and not is_http_url(str(homepage)):
            raise ConfigurationError(f"Homepage URL is not HTTP(S): {feed_id}")
        if item.get("image_policy", "rss_only") != "rss_only":
            raise ConfigurationError(f"Only rss_only image policy is permitted: {feed_id}")
        max_items = int(item.get("max_items_per_run", 5))
        if not 1 <= max_items <= 20:
            raise ConfigurationError(f"max_items_per_run must be between 1 and 20: {feed_id}")
        categories = item.get("categories", [])
        if not isinstance(categories, list):
            raise ConfigurationError(f"categories must be a list: {feed_id}")
        configs.append(
            FeedConfig(
                id=feed_id,
                name=str(item["name"]),
                url=str(item["url"]),
                homepage=str(homepage) if homepage else None,
                language=str(item["language"]),
                enabled=bool(item["enabled"]),
                priority=int(item["priority"]),
                max_items_per_run=max_items,
                image_policy="rss_only",
                categories=tuple(str(category) for category in categories),
            )
        )
        seen_ids.add(feed_id)
    return sorted(configs, key=lambda config: config.priority, reverse=True)


def load_json(path: Path, default: dict[str, Any]) -> dict[str, Any]:
    if not path.exists():
        return default
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Invalid JSON in {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"JSON root in {path} must be an object")
    return value


def write_json_atomic(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as temporary_file:
            json.dump(value, temporary_file, ensure_ascii=False, indent=2, sort_keys=True)
            temporary_file.write("\n")
            temporary_file.flush()
            os.fsync(temporary_file.fileno())
        os.replace(temporary_name, path)
    except Exception:
        try:
            os.unlink(temporary_name)
        except FileNotFoundError:
            pass
        raise


def parse_frontmatter(path: Path) -> dict[str, Any]:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ValueError(f"Could not read Markdown {path}: {exc}") from exc
    match = FRONTMATTER_RE.match(text)
    if not match:
        raise ValueError(f"Markdown is missing YAML frontmatter: {path}")
    try:
        data = yaml.safe_load(match.group(1))
    except yaml.YAMLError as exc:
        raise ValueError(f"Invalid YAML frontmatter in {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError(f"Frontmatter root must be an object: {path}")
    return data


def recover_dedupe_keys(content_dir: Path) -> set[str]:
    keys: set[str] = set()
    if not content_dir.exists():
        return keys
    for path in content_dir.rglob("*.md"):
        data = parse_frontmatter(path)
        if isinstance(data.get("dedupeKey"), str) and data["dedupeKey"]:
            keys.add(data["dedupeKey"])
        # Keep recovery compatible with a checkout that still has legacy daily files.
        items = data.get("items", [])
        if isinstance(items, list):
            for item in items:
                if isinstance(item, dict) and isinstance(item.get("dedupeKey"), str):
                    keys.add(item["dedupeKey"])
    return keys


def recover_article_metadata(content_dir: Path) -> dict[str, dict[str, Any]]:
    """Recover minimal seen-state metadata from immutable article frontmatter."""
    recovered: dict[str, dict[str, Any]] = {}
    if not content_dir.exists():
        return recovered
    for path in content_dir.rglob("*.md"):
        data = parse_frontmatter(path)
        key = data.get("dedupeKey")
        if not isinstance(key, str) or not key:
            continue
        recovered[key] = {
            "url": data.get("canonicalUrl") or data.get("sourceUrl"),
            "source": data.get("sourceId"),
            "published_at": data.get("publishedAt"),
            "first_seen_at": data.get("generatedAt"),
            "article_id": data.get("articleId"),
        }
    return recovered
