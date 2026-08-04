from __future__ import annotations

import hashlib
import re
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import yaml

from scripts.models import PreparedItem
from scripts.translation_quality import QUALITY_GATE_REASON_CODES
from scripts.utils import is_http_url, parse_frontmatter

JST = ZoneInfo("Asia/Tokyo")
ARTICLE_ID_RE = re.compile(r"[a-z0-9][a-z0-9-]*-[0-9a-f]{8}")


class ContentValidationError(ValueError):
    """Raised when generated Markdown violates the public content schema."""


def japanese_date(date_value: str) -> str:
    year, month, day = (int(part) for part in date_value.split("-"))
    return f"{year}年{month}月{day}日"


def article_id_for(source_id: str, dedupe_key: str) -> str:
    """Return an ID that is stable even when a translated title is edited."""
    safe_source = re.sub(r"[^a-z0-9-]+", "-", source_id.lower()).strip("-") or "article"
    digest = hashlib.sha256(dedupe_key.encode("utf-8")).hexdigest()[:8]
    return f"{safe_source}-{digest}"


def article_relative_path(date_value: str, article_id: str) -> Path:
    return Path(date_value) / f"{article_id}.md"


def build_brief(item: Any, summary_ja: str) -> str:
    published_jst = item.published_at.astimezone(JST)
    date_text = f"{published_jst.month}月{published_jst.day}日"
    prefix = f"{item.source_name}は{date_text}、「{item.title_ja}」を公式フィードで発表しました。"
    if summary_ja:
        summary = summary_ja.strip().rstrip("。.!！")
        middle = f"公式RSSによると、{summary}。"
    else:
        middle = "概要の翻訳を掲載できないため、発表内容は公式リンクでご確認ください。"
    suffix = (
        "内容は自動翻訳・定型編集されています。詳細や正確な仕様は、"
        "リンク先の公式発表をご確認ください。"
    )
    available = 320 - len(prefix) - len(suffix) - len("公式RSSによると、。")
    if summary_ja and available < len(summary):
        summary = f"{summary[: max(1, available - 1)].rstrip()}…"
        middle = f"公式RSSによると、{summary}。"
    brief = prefix + middle + suffix
    if len(brief) < 120:
        brief += "原文タイトルと配信元も併記しています。"
    return brief[:320]


def build_excerpt(brief_ja: str, maximum: int = 120) -> str:
    """Make the daily collection view an excerpt rather than a second article body."""
    text = brief_ja.split("内容は自動翻訳", 1)[0].strip().rstrip("。")
    if len(text) <= maximum:
        return text
    return f"{text[: maximum - 1].rstrip()}…"


def _description(item: PreparedItem) -> str:
    text = item.brief_ja.strip()
    if len(text) > 160:
        candidate = text[:160]
        boundary = max(candidate.rfind("。"), candidate.rfind("！"), candidate.rfind("？"))
        text = candidate[: boundary + 1] if boundary >= 119 else f"{candidate[:159].rstrip()}…"
    if len(text) < 120:
        text = (
            f"{item.title_ja}。{item.source_name}の公式RSSをもとにした日本語短報です。"
            "原文タイトルと公式発表へのリンクを併記しています。"
        )
    return text[:160]


def article_data_from_item(
    item: PreparedItem,
    *,
    generated_at: datetime,
    generated_iso: str | None = None,
    created_iso: str | None = None,
) -> dict[str, Any]:
    date_value = item.published_at.astimezone(JST).date().isoformat()
    generated = generated_iso or generated_at.astimezone(JST).isoformat(timespec="seconds")
    created = created_iso or generated
    fetched = (
        item.fetched_at.astimezone(JST).isoformat(timespec="seconds")
        if item.fetched_at
        else generated
    )
    article_id = article_id_for(item.source_id, item.dedupe_key)
    return {
        "articleId": article_id,
        "titleJa": item.title_ja,
        "titleOriginal": item.title_original,
        "description": _description(item),
        "briefJa": item.brief_ja,
        "excerptJa": item.excerpt_ja or build_excerpt(item.brief_ja),
        "publishedAt": item.published_at.isoformat().replace("+00:00", "Z"),
        "dateJst": date_value,
        "sourceId": item.source_id,
        "sourceName": item.source_name,
        "sourceHomepage": item.source_homepage,
        "sourceUrl": item.url,
        "canonicalUrl": item.canonical_url,
        "imageUrl": item.image_url,
        "imageLicense": item.image_license,
        "author": item.author,
        "translationStatus": item.translation_status,
        "titleTranslationStatus": item.title_translation_status,
        "summaryTranslationStatus": item.summary_translation_status,
        "titleQualityGate": item.title_quality_gate,
        "summaryQualityGate": item.summary_quality_gate,
        "titleFallbackApplied": item.title_fallback_applied,
        "summaryFallbackApplied": item.summary_fallback_applied,
        "titleFallbackReasons": list(item.title_fallback_reasons),
        "summaryFallbackReasons": list(item.summary_fallback_reasons),
        "translationFallbackReasons": sorted(
            set(item.title_fallback_reasons) | set(item.summary_fallback_reasons)
        ),
        "dedupeKey": item.dedupe_key,
        "fetchedAt": fetched,
        "generatedAt": created,
        "updatedAt": generated,
        "humanEdited": False,
        "correctionHistory": [],
        "noindex": False,
    }


def validate_article_data(data: dict[str, Any]) -> None:
    required = {
        "articleId",
        "titleJa",
        "titleOriginal",
        "description",
        "briefJa",
        "excerptJa",
        "publishedAt",
        "dateJst",
        "sourceId",
        "sourceName",
        "sourceUrl",
        "canonicalUrl",
        "translationStatus",
        "dedupeKey",
        "fetchedAt",
        "generatedAt",
        "updatedAt",
        "humanEdited",
        "correctionHistory",
        "noindex",
    }
    missing = required - data.keys()
    if missing:
        raise ContentValidationError(f"Missing article frontmatter keys: {sorted(missing)}")
    if not isinstance(data["articleId"], str) or not ARTICLE_ID_RE.fullmatch(data["articleId"]):
        raise ContentValidationError("articleId must be a stable source-id plus eight-hex-id")
    for key in ("titleJa", "titleOriginal", "briefJa", "excerptJa", "sourceId", "sourceName"):
        if not isinstance(data[key], str) or not data[key].strip():
            raise ContentValidationError(f"{key} must be a non-empty string")
    if not isinstance(data["description"], str) or not 80 <= len(data["description"]) <= 160:
        raise ContentValidationError("Article description must be between 80 and 160 characters")
    if not isinstance(data["briefJa"], str) or not 120 <= len(data["briefJa"]) <= 320:
        raise ContentValidationError("Every Japanese brief must be 120 to 320 characters")
    if not isinstance(data["excerptJa"], str) or not data["excerptJa"].strip():
        raise ContentValidationError("Every article needs a daily-view excerpt")
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(data["dateJst"])):
        raise ContentValidationError("dateJst must be YYYY-MM-DD")
    for key in ("sourceUrl", "canonicalUrl"):
        if not is_http_url(str(data[key])):
            raise ContentValidationError(f"{key} must be an HTTP(S) URL")
    if data["translationStatus"] not in {"complete", "partial"}:
        raise ContentValidationError("translationStatus must be complete or partial")
    translation_statuses = {
        "legacy",
        "translated",
        "fallback",
        "rejected",
        "failed",
        "missing",
        "quality_rejected",
        "translation_failed",
        "source_missing",
    }
    for key in ("titleTranslationStatus", "summaryTranslationStatus"):
        if key in data and data[key] not in translation_statuses:
            raise ContentValidationError(f"{key} has an unsupported value")
    for key in ("titleQualityGate", "summaryQualityGate"):
        if key in data and data[key] not in {"passed", "rejected", "not_run"}:
            raise ContentValidationError(f"{key} has an unsupported value")
    for key in (
        "titleFallbackApplied",
        "summaryFallbackApplied",
    ):
        if key in data and not isinstance(data[key], bool):
            raise ContentValidationError(f"{key} must be a boolean")
    for key in (
        "titleFallbackReasons",
        "summaryFallbackReasons",
        "translationFallbackReasons",
    ):
        if key in data and (
            not isinstance(data[key], list)
            or not all(isinstance(reason, str) and reason for reason in data[key])
        ):
            raise ContentValidationError(f"{key} must be a list of non-empty strings")
        if key in data and any(reason not in QUALITY_GATE_REASON_CODES for reason in data[key]):
            raise ContentValidationError(f"{key} contains an unknown quality reason code")
    if not isinstance(data["dedupeKey"], str) or not data["dedupeKey"].strip():
        raise ContentValidationError("dedupeKey must be non-empty")
    if not isinstance(data["humanEdited"], bool) or not isinstance(data["noindex"], bool):
        raise ContentValidationError("humanEdited and noindex must be booleans")
    if not isinstance(data["correctionHistory"], list):
        raise ContentValidationError("correctionHistory must be a list")


def render_article_markdown(data: dict[str, Any]) -> str:
    """Render frontmatter-only Markdown; frontmatter is the article source of truth."""
    validate_article_data(data)
    frontmatter = yaml.safe_dump(
        data,
        allow_unicode=True,
        sort_keys=False,
        width=1000,
        default_flow_style=False,
    ).strip()
    return f"---\n{frontmatter}\n---\n"


def write_article_files(
    items: list[PreparedItem],
    *,
    existing_dir: Path,
    output_dir: Path,
    generated_at: datetime,
) -> list[Path]:
    """Stage one immutable Markdown file per new article."""
    output_dir.mkdir(parents=True, exist_ok=True)
    generated_paths: list[Path] = []
    generated_iso = generated_at.astimezone(JST).isoformat(timespec="seconds")
    seen_paths: set[Path] = set()
    for item in sorted(items, key=lambda value: value.published_at, reverse=True):
        date_value = item.published_at.astimezone(JST).date().isoformat()
        article_id = article_id_for(item.source_id, item.dedupe_key)
        relative_path = article_relative_path(date_value, article_id)
        if relative_path in seen_paths:
            raise ContentValidationError(
                f"Article path collision in generation batch: {relative_path}"
            )
        seen_paths.add(relative_path)
        existing_path = existing_dir / relative_path
        if existing_path.exists():
            existing = parse_frontmatter(existing_path)
            if existing.get("dedupeKey") != item.dedupe_key:
                raise ContentValidationError(f"Article ID collision: {relative_path}")
            continue
        data = article_data_from_item(item, generated_at=generated_at, generated_iso=generated_iso)
        output_path = output_dir / relative_path
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(render_article_markdown(data), encoding="utf-8")
        validate_article_data(parse_frontmatter(output_path))
        generated_paths.append(relative_path)
    return generated_paths
