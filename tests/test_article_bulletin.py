from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_article_bulletin_exposes_public_metadata_without_reason_codes() -> None:
    component = (ROOT / "src/components/ArticleBulletin.astro").read_text(encoding="utf-8")

    for phrase in (
        "外電票",
        "原文タイトル",
        "AI外電取得日時",
        "AI外電初回生成日時",
        "最終更新日時",
        "タイトル翻訳",
        "概要翻訳",
        "フォールバック",
        "人間修正",
        "公式発表",
        "correctionHistory",
        "訂正・更新履歴",
    ):
        assert phrase in component
    assert "titleFallbackReasons" not in component
    assert "summaryFallbackReasons" not in component


def test_article_page_reuses_the_bulletin_component() -> None:
    article = (
        ROOT / "src/pages/articles/[year]/[month]/[day]/[slug].astro"
    ).read_text(encoding="utf-8")

    assert "import ArticleBulletin" in article
    assert "<ArticleBulletin data={data} />" in article
    assert '<dl class="article-facts">' not in article
