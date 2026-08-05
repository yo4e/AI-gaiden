from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

from scripts.content_writer import article_data_from_item, render_article_markdown
from scripts.models import FeedConfig
from scripts.utils import load_feed_configs
from scripts.validate_repository import validate_articles, validate_source_consistency

ROOT = Path(__file__).resolve().parents[1]


def make_validation_item():
    from scripts.models import PreparedItem

    return PreparedItem(
        source_id="example-ai",
        source_name="Example AI",
        title_ja="研究ツールキットの更新を公開",
        title_original="Research toolkit update",
        brief_ja="公式RSSによる研究ツールキットの更新内容を日本語で紹介します。自動翻訳・定型編集の短報です。公式発表の背景と対象範囲を確認できる内容であり、重要な仕様は原文へのリンクを参照する必要があります。今回の更新に関する詳細な条件や利用方法も原文で確認できます。",
        url="https://example.com/posts/toolkit",
        canonical_url="https://example.com/posts/toolkit",
        published_at=datetime(2026, 8, 3, 0, 30, tzinfo=UTC),
        image_url=None,
        image_license=None,
        author="Example Labs",
        translation_status="complete",
        dedupe_key="url:fixture-key",
        source_homepage="https://example.com/",
    )


def test_historical_article_from_disabled_configured_source_is_valid(tmp_path) -> None:
    item = make_validation_item()
    data = article_data_from_item(item, generated_at=datetime(2026, 8, 3, 3, 0, tzinfo=UTC))
    articles = tmp_path / "articles" / data["dateJst"]
    articles.mkdir(parents=True)
    (articles / f"{data['articleId']}.md").write_text(
        render_article_markdown(data), encoding="utf-8"
    )
    config = FeedConfig(
        id="example-ai",
        name="Example AI",
        url="https://example.com/feed.xml",
        homepage="https://example.com/",
        language="en",
        enabled=False,
        priority=1,
        max_items_per_run=5,
        image_policy="rss_only",
        categories=("ai",),
    )

    article_count, dedupe_keys, article_ids = validate_articles(tmp_path / "articles", [config])

    assert article_count == 1
    assert dedupe_keys == {data["dedupeKey"]}
    assert article_ids == {data["articleId"]}


def test_site_source_catalog_matches_feed_configuration() -> None:
    configs = load_feed_configs(ROOT / "config/feeds.yml")
    source_text = (ROOT / "src/data/sources.ts").read_text(encoding="utf-8")

    assert validate_source_consistency(configs, source_text) == len(configs)


def test_site_source_catalog_rejects_feed_url_drift() -> None:
    configs = load_feed_configs(ROOT / "config/feeds.yml")
    source_text = (ROOT / "src/data/sources.ts").read_text(encoding="utf-8")
    changed = source_text.replace(
        "feedUrl: 'https://openai.com/news/rss.xml'",
        "feedUrl: 'https://example.com/incorrect.xml'",
        1,
    )

    with pytest.raises(ValueError, match="Source metadata differs for openai-news"):
        validate_source_consistency(configs, changed)
