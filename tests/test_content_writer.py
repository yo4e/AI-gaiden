from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime

import pytest

from scripts.content_writer import (
    ContentValidationError,
    article_data_from_item,
    article_id_for,
    build_brief,
    render_article_markdown,
    validate_article_data,
    write_article_files,
)
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
        "source_homepage": "https://example.com/",
    }
    values.update(overrides)
    return PreparedItem(**values)


def test_brief_has_required_length_and_disclosure() -> None:
    item = make_item()
    brief = build_brief(item, "公式リリースでは、文書化された研究用ツールが追加されています")

    assert 120 <= len(brief) <= 320
    assert "自動翻訳・定型編集" in brief
    assert "公式発表" in brief


def test_article_id_is_stable_when_translated_title_changes() -> None:
    key = "url:fixture-key"
    assert article_id_for("example-ai", key) == article_id_for("example-ai", key)
    assert article_id_for("example-ai", key) != article_id_for("example-ai", "url:other")


def test_writes_one_immutable_article_file_per_item(tmp_path) -> None:
    existing_dir = tmp_path / "existing"
    output_dir = tmp_path / "output"
    existing_dir.mkdir()
    generated_at = datetime(2026, 8, 3, 3, 0, tzinfo=UTC)

    first_base = make_item()
    first = replace(
        first_base,
        brief_ja=build_brief(first_base, "最初の公式概要を日本語化した内容です"),
    )
    first_paths = write_article_files(
        [first], existing_dir=existing_dir, output_dir=output_dir, generated_at=generated_at
    )
    assert len(first_paths) == 1
    first_path = output_dir / first_paths[0]
    (existing_dir / first_paths[0]).parent.mkdir(parents=True)
    first_path.replace(existing_dir / first_paths[0])

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
    merged_paths = write_article_files(
        [first, second], existing_dir=existing_dir, output_dir=merged_dir, generated_at=generated_at
    )

    assert len(merged_paths) == 1
    data = parse_frontmatter(merged_dir / merged_paths[0])
    validate_article_data(data)
    assert data["dedupeKey"] == "url:second-key"
    assert data["articleId"] == article_id_for("example-ai", "url:second-key")


def test_same_generation_batch_article_path_collision_raises(tmp_path) -> None:
    base = make_item(
        brief_ja=build_brief(make_item(), "同じURLの公式概要を日本語化した内容です")
    )
    conflicting = replace(base, title_ja="別の翻訳タイトル")

    with pytest.raises(ContentValidationError, match="collision in generation batch"):
        write_article_files(
            [base, conflicting],
            existing_dir=tmp_path / "existing",
            output_dir=tmp_path / "output",
            generated_at=datetime(2026, 8, 3, 3, 0, tzinfo=UTC),
        )


def test_generated_markdown_has_no_duplicate_body() -> None:
    item = make_item(
        brief_ja=build_brief(make_item(), "本文を生成しない正本設計を確認する公式概要です")
    )
    data = article_data_from_item(
        item, generated_at=datetime(2026, 8, 3, 3, 0, tzinfo=UTC)
    )

    assert render_article_markdown(data).split("---", 2)[-1].strip() == ""
