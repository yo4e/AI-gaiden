from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_sources_entrypoint_lists_all_source_metadata_and_counts() -> None:
    page = (ROOT / "src/pages/sources.astro").read_text(encoding="utf-8")
    card = (ROOT / "src/components/SourceCard.astro").read_text(encoding="utf-8")
    implementation = page + card

    for phrase in (
        "getCollection('articles')",
        "articleCounts",
        "publishedSources",
        "preparingSources",
        "準備中・一時停止",
        "source.categories",
        "sourceCategoryLabel",
        "sourceImagePolicyLabel",
        "掲載記事数",
        "配信元ページを見る",
        "取得対象",
    ):
        assert phrase in implementation


def test_source_detail_page_has_stable_urls_and_thin_page_policy() -> None:
    page = (ROOT / "src/pages/sources/[sourceId].astro").read_text(encoding="utf-8")

    for phrase in (
        "params: { sourceId: source.id }",
        "source.feedUrl",
        "source.homepage",
        "source.enabled",
        "source.categories",
        "source.imagePolicy",
        "sourceCategoryLabel",
        "sourceImagePolicyLabel",
        "最新記事一覧",
        "<NewsCard article={article} />",
        "const isThin = articleCount < 2",
        "noindex={isThin}",
        "sitemapにも収録しません",
        "canonicalPath",
        "取得対象",
    ):
        assert phrase in page


def test_source_metadata_uses_reader_facing_labels() -> None:
    presentation = (ROOT / "src/lib/sourcePresentation.ts").read_text(encoding="utf-8")

    for phrase in (
        "'artificial-intelligence': 'AI'",
        "'machine-learning': '機械学習'",
        "'developer-tools': '開発者向けツール'",
        "'rss_only'",
        "公式RSS・Atomに明示された画像のみ",
    ):
        assert phrase in presentation

    for path in ("src/pages/sources.astro", "src/pages/sources/[sourceId].astro"):
        page = (ROOT / path).read_text(encoding="utf-8")
        assert "（{source.imagePolicy}）" not in page
        assert "source.categories.join('、')" not in page


def test_article_source_links_use_source_detail_pages() -> None:
    badge = (ROOT / "src/components/SourceBadge.astro").read_text(encoding="utf-8")
    bulletin = (ROOT / "src/components/ArticleBulletin.astro").read_text(encoding="utf-8")

    assert "`/sources/${id}/`" in badge
    assert "`/sources/${data.sourceId}/`" in bulletin
    assert "/sources/#" not in badge + bulletin
