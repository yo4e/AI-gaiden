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


def test_article_bulletin_does_not_treat_legacy_state_as_a_fallback() -> None:
    component = (ROOT / "src/components/ArticleBulletin.astro").read_text(encoding="utf-8")

    assert "詳細な翻訳状態の記録なし" in component
    assert "status !== 'translated'" not in component
    assert "legacySummaryFallback" in component
    assert "概要の翻訳を掲載できないため" in component


def test_public_correction_dates_require_an_explicit_iso_timezone() -> None:
    component = (ROOT / "src/components/ArticleBulletin.astro").read_text(encoding="utf-8")

    assert "OFFSET_DATETIME_RE" in component
    assert "(?:Z|[+-]\\d{2}:\\d{2})" in component
    assert "validDateOnly(value.slice(0, 10))" in component
    assert "validCorrectionDate(date)" in component


def test_article_page_reuses_the_bulletin_component() -> None:
    article = (
        ROOT / "src/pages/articles/[year]/[month]/[day]/[slug].astro"
    ).read_text(encoding="utf-8")

    assert "import ArticleBulletin" in article
    assert "<ArticleBulletin data={data} />" in article
    assert '<dl class="article-facts">' not in article
