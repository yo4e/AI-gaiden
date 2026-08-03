from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime

from scripts.content_writer import build_brief, validate_daily_data, write_daily_pages
from scripts.models import PreparedItem
from scripts.utils import parse_frontmatter


def make_item(**overrides) -> PreparedItem:
    values = {
        "source_id": "example-ai",
        "source_name": "Example AI",
        "title_ja": "研究ツールキットの更新を公開",
        "title_original": "Research toolkit update",
        "brief_ja": "placeholder",
        "url": "https://example.com/posts/toolkit",
        "canonical_url": "https://example.com/posts/toolkit",
        "published_at": datetime(2026, 8, 3, 0, 30, tzinfo=UTC),
        "image_url": "https://cdn.example.com/toolkit.png",
        "image_license": None,
        "author": "Example Labs",
        "translation_status": "complete",
        "dedupe_key": "url:fixture-key",
    }
    values.update(overrides)
    return PreparedItem(**values)


def test_brief_has_required_length_and_disclosure() -> None:
    item = make_item()
    brief = build_brief(item, "公式リリースでは、文書化された研究用ツールが追加されています")

    assert 120 <= len(brief) <= 320
    assert "自動翻訳・定型編集" in brief
    assert "公式発表" in brief


def test_writes_valid_frontmatter_and_merges_existing_day(tmp_path) -> None:
    existing_dir = tmp_path / "existing"
    output_dir = tmp_path / "output"
    existing_dir.mkdir()
    generated_at = datetime(2026, 8, 3, 3, 0, tzinfo=UTC)

    first = make_item(brief_ja=build_brief(make_item(), "最初の公式概要を日本語化した内容です"))
    first_paths = write_daily_pages(
        [first], existing_dir=existing_dir, output_dir=output_dir, generated_at=generated_at
    )
    first_path = first_paths[0]
    first_path.replace(existing_dir / first_path.name)

    second_base = make_item(
        title_ja="別の公式発表",
        title_original="Another official release",
        url="https://example.com/posts/another",
        canonical_url="https://example.com/posts/another",
        dedupe_key="url:second-key",
        published_at=datetime(2026, 8, 3, 1, 0, tzinfo=UTC),
    )
    second = replace(
        second_base,
        brief_ja=build_brief(second_base, "二つ目の公式概要を日本語化した内容です"),
    )
    merged_dir = tmp_path / "merged"
    merged_path = write_daily_pages(
        [second], existing_dir=existing_dir, output_dir=merged_dir, generated_at=generated_at
    )[0]
    data = parse_frontmatter(merged_path)

    validate_daily_data(data)
    assert data["itemCount"] == 2
    assert len(data["description"]) in range(120, 161)
    assert {item["dedupeKey"] for item in data["items"]} == {
        "url:fixture-key",
        "url:second-key",
    }
