from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class FeedConfig:
    id: str
    name: str
    url: str
    homepage: str | None
    language: str
    enabled: bool
    priority: int
    max_items_per_run: int
    image_policy: str
    categories: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class NormalizedItem:
    source_id: str
    source_name: str
    title: str
    url: str
    canonical_url: str
    guid: str | None
    published_at: datetime | None
    date_status: str
    summary: str
    author: str | None
    image_url: str | None
    image_license: str | None
    dedupe_key: str
    source_homepage: str | None = None


@dataclass(frozen=True, slots=True)
class PreparedItem:
    source_id: str
    source_name: str
    title_ja: str
    title_original: str
    brief_ja: str
    url: str
    canonical_url: str
    published_at: datetime
    image_url: str | None
    image_license: str | None
    author: str | None
    translation_status: str
    dedupe_key: str
    source_homepage: str | None = None
    fetched_at: datetime | None = None
    excerpt_ja: str | None = None
    title_translation_status: str = "legacy"
    summary_translation_status: str = "legacy"
    title_quality_gate: str = "not_run"
    summary_quality_gate: str = "not_run"
    title_fallback_applied: bool = False
    summary_fallback_applied: bool = False
    title_fallback_reasons: tuple[str, ...] = ()
    summary_fallback_reasons: tuple[str, ...] = ()
