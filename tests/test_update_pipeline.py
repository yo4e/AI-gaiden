from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

from scripts.feed_reader import FeedResult, parse_feed_bytes
from scripts.models import FeedConfig
from scripts.translator import TranslationError, Translator
from scripts.updater import UpdateError, run_update
from scripts.utils import parse_frontmatter


class FixtureReader:
    def __init__(self, results: list[FeedResult]) -> None:
        self.results = results

    def fetch_all(self, _configs: list[FeedConfig]) -> list[FeedResult]:
        return self.results


class JapaneseFixtureTranslator(Translator):
    def translate(self, text: str) -> str:
        if "Example Model" in text:
            return "Example Model v2.1が利用可能になりました"
        if "GUID-only" in text:
            return "公式フィードの追加情報"
        return "公式RSSには、研究タスク向けのモデルと評価に関する説明が掲載されています"


class AlwaysFailTranslator(Translator):
    def translate(self, text: str) -> str:
        raise TranslationError(f"fixture failure: {text[:10]}")


def write_config(path: Path) -> None:
    path.write_text(
        """feeds:
  - id: example-ai
    name: Example AI
    url: https://example.com/feed.xml
    homepage: https://example.com/
    language: en
    enabled: true
    priority: 100
    max_items_per_run: 10
    image_policy: rss_only
    categories: [ai]
""",
        encoding="utf-8",
    )


def test_fixture_to_japanese_daily_markdown_and_deduplication(
    tmp_path, fixture_dir, feed_config
) -> None:
    config_path = tmp_path / "feeds.yml"
    seen_path = tmp_path / "seen.json"
    content_dir = tmp_path / "daily"
    write_config(config_path)
    seen_path.write_text('{"items": {}}\n', encoding="utf-8")
    items = parse_feed_bytes((fixture_dir / "rss.xml").read_bytes(), feed_config)
    reader = FixtureReader([FeedResult(feed_config, True, False, tuple(items))])
    now = datetime(2026, 8, 3, 3, 0, tzinfo=UTC)

    count = run_update(
        config_path=config_path,
        seen_path=seen_path,
        content_dir=content_dir,
        cache_path=tmp_path / "cache.json",
        bootstrap_days=3,
        now=now,
        reader=reader,
        translator=JapaneseFixtureTranslator(),
    )

    assert count == 2
    page = content_dir / "2026-08-03.md"
    assert page.exists()
    data = parse_frontmatter(page)
    assert data["itemCount"] == 2
    assert all("公式発表" in item["briefJa"] for item in data["items"])

    second_count = run_update(
        config_path=config_path,
        seen_path=seen_path,
        content_dir=content_dir,
        cache_path=tmp_path / "cache.json",
        bootstrap_days=3,
        now=now,
        reader=reader,
        translator=JapaneseFixtureTranslator(),
    )
    assert second_count == 0
    assert parse_frontmatter(page)["itemCount"] == 2


def test_all_feed_failures_leave_existing_files_unchanged(tmp_path, feed_config) -> None:
    config_path = tmp_path / "feeds.yml"
    seen_path = tmp_path / "seen.json"
    content_dir = tmp_path / "daily"
    content_dir.mkdir()
    write_config(config_path)
    seen_path.write_text('{"items": {"existing": {}}}\n', encoding="utf-8")
    sentinel = content_dir / "sentinel.txt"
    sentinel.write_text("unchanged", encoding="utf-8")
    reader = FixtureReader([FeedResult(feed_config, False, False, (), "network down")])

    with pytest.raises(UpdateError, match="All enabled feeds failed"):
        run_update(
            config_path=config_path,
            seen_path=seen_path,
            content_dir=content_dir,
            cache_path=tmp_path / "cache.json",
            bootstrap_days=3,
            reader=reader,
            translator=AlwaysFailTranslator(),
        )

    assert sentinel.read_text(encoding="utf-8") == "unchanged"
    assert seen_path.read_text(encoding="utf-8") == '{"items": {"existing": {}}}\n'
