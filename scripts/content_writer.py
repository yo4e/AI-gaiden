from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import yaml

from scripts.models import PreparedItem
from scripts.utils import parse_frontmatter

JST = ZoneInfo("Asia/Tokyo")
DISCLOSURE = (
    "この日次ダイジェストは、公式RSSのタイトルと短い概要を自動翻訳し、"
    "事実を追加しない定型文で編集しています。正確な内容は各公式発表をご確認ください。"
)


class ContentValidationError(ValueError):
    """Raised when generated Markdown violates the public content schema."""


def japanese_date(date_value: str) -> str:
    year, month, day = (int(part) for part in date_value.split("-"))
    return f"{year}年{month}月{day}日"


def build_brief(item: NormalizedForBrief, summary_ja: str) -> str:
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


class NormalizedForBrief:
    """Structural typing helper for title/source/date fields used by build_brief."""

    source_name: str
    title_ja: str
    published_at: datetime


def _item_to_frontmatter(item: PreparedItem) -> dict[str, Any]:
    return {
        "titleJa": item.title_ja,
        "titleOriginal": item.title_original,
        "briefJa": item.brief_ja,
        "url": item.url,
        "sourceId": item.source_id,
        "sourceName": item.source_name,
        "publishedAt": item.published_at.isoformat().replace("+00:00", "Z"),
        "imageUrl": item.image_url,
        "imageLicense": item.image_license,
        "author": item.author,
        "translationStatus": item.translation_status,
        "dedupeKey": item.dedupe_key,
    }


def _description(date_value: str, items: list[dict[str, Any]]) -> str:
    source_names = list(dict.fromkeys(str(item["sourceName"]) for item in items))
    headlines = "、".join(_shorten(str(item["titleJa"]), 28) for item in items[:2])
    text = (
        f"{japanese_date(date_value)}に{('、'.join(source_names))}が公式配信した海外AIニュース"
        f"{len(items)}件を日本語で紹介します。{headlines}などの発表をまとめています。"
    )
    supplement = (
        "各項目に原文タイトル、配信元、公開日時、公式リンクを併記し、"
        "自動翻訳の内容を原文と照合できます。"
    )
    if len(text) < 120:
        text += supplement
    if len(text) < 120:
        text += "重要な情報はリンク先の公式発表で確認してください。"
    if len(text) > 160:
        text = f"{text[:159].rstrip('、。 ')}。"
    return text


def _shorten(value: str, maximum: int) -> str:
    return value if len(value) <= maximum else f"{value[: maximum - 1]}…"


def _title(date_value: str, items: list[dict[str, Any]]) -> str:
    headline = _shorten(str(items[0]["titleJa"]), 32)
    return f"海外AIニュース {japanese_date(date_value)}｜{headline}｜AI外電"


def _load_existing(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return parse_frontmatter(path)


def validate_daily_data(data: dict[str, Any]) -> None:
    required = {
        "title",
        "description",
        "date",
        "publishedAt",
        "updatedAt",
        "itemCount",
        "sources",
        "noindex",
        "items",
    }
    if required - data.keys():
        raise ContentValidationError(f"Missing frontmatter keys: {sorted(required - data.keys())}")
    items = data["items"]
    if not isinstance(items, list) or not items or data["itemCount"] != len(items):
        raise ContentValidationError("itemCount must match a non-empty items list")
    if not isinstance(data["description"], str) or not 120 <= len(data["description"]) <= 160:
        raise ContentValidationError("Description must be between 120 and 160 characters")
    dedupe_keys: set[str] = set()
    for item in items:
        if not isinstance(item, dict):
            raise ContentValidationError("Every item must be an object")
        key = item.get("dedupeKey")
        if not isinstance(key, str) or not key or key in dedupe_keys:
            raise ContentValidationError("Every item needs a unique dedupeKey")
        dedupe_keys.add(key)
        brief = item.get("briefJa")
        if not isinstance(brief, str) or not 120 <= len(brief) <= 320:
            raise ContentValidationError("Every Japanese brief must be 120 to 320 characters")
        if not str(item.get("url", "")).startswith(("https://", "http://")):
            raise ContentValidationError("Every item needs an HTTP(S) official URL")


def render_daily_markdown(data: dict[str, Any]) -> str:
    validate_daily_data(data)
    frontmatter = yaml.safe_dump(
        data,
        allow_unicode=True,
        sort_keys=False,
        width=1000,
        default_flow_style=False,
    ).strip()
    return f"---\n{frontmatter}\n---\n\n{DISCLOSURE}\n"


def write_daily_pages(
    items: list[PreparedItem],
    *,
    existing_dir: Path,
    output_dir: Path,
    generated_at: datetime,
) -> list[Path]:
    grouped: dict[str, list[PreparedItem]] = defaultdict(list)
    for item in items:
        date_value = item.published_at.astimezone(JST).date().isoformat()
        grouped[date_value].append(item)

    output_dir.mkdir(parents=True, exist_ok=True)
    generated_paths: list[Path] = []
    generated_iso = generated_at.astimezone(JST).isoformat(timespec="seconds")
    for date_value, new_items in sorted(grouped.items()):
        existing_path = existing_dir / f"{date_value}.md"
        existing = _load_existing(existing_path)
        old_items = existing.get("items", []) if existing else []
        if not isinstance(old_items, list):
            raise ContentValidationError(f"Existing items must be a list: {existing_path}")
        combined = [item for item in old_items if isinstance(item, dict)]
        existing_keys = {str(item.get("dedupeKey")) for item in combined}
        combined.extend(
            _item_to_frontmatter(item)
            for item in new_items
            if item.dedupe_key not in existing_keys
        )
        combined.sort(key=lambda item: str(item["publishedAt"]), reverse=True)
        sources = list(dict.fromkeys(str(item["sourceId"]) for item in combined))
        data = {
            "title": _title(date_value, combined),
            "description": _description(date_value, combined),
            "date": date_value,
            "publishedAt": (
                existing.get("publishedAt", generated_iso) if existing else generated_iso
            ),
            "updatedAt": generated_iso,
            "itemCount": len(combined),
            "sources": sources,
            "noindex": False,
            "items": combined,
        }
        output_path = output_dir / f"{date_value}.md"
        output_path.write_text(render_daily_markdown(data), encoding="utf-8")
        # Parse the serialized file as a final schema-independent syntax check.
        validate_daily_data(parse_frontmatter(output_path))
        generated_paths.append(output_path)
    return generated_paths
