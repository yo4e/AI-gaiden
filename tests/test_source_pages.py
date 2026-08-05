from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_sources_entrypoint_lists_all_source_metadata_and_counts() -> None:
    page = (ROOT / "src/pages/sources.astro").read_text(encoding="utf-8")

    for phrase in (
        "getCollection('articles')",
        "articleCounts",
        "source.categories",
        "掲載記事数",
        "配信元ページを見る",
    ):
        assert phrase in page


def test_source_detail_page_has_stable_urls_and_thin_page_policy() -> None:
    page = (ROOT / "src/pages/sources/[sourceId].astro").read_text(encoding="utf-8")

    for phrase in (
        "params: { sourceId: source.id }",
        "source.feedUrl",
        "source.homepage",
        "source.enabled",
        "source.categories",
        "source.imagePolicy",
        "最新記事一覧",
        "<NewsCard article={article} />",
        "const isThin = articleCount < 2",
        "noindex={isThin}",
        "sitemapにも収録しません",
        "canonicalPath",
    ):
        assert phrase in page


def test_article_source_links_use_source_detail_pages() -> None:
    badge = (ROOT / "src/components/SourceBadge.astro").read_text(encoding="utf-8")
    bulletin = (ROOT / "src/components/ArticleBulletin.astro").read_text(encoding="utf-8")

    assert "`/sources/${id}/`" in badge
    assert "`/sources/${data.sourceId}/`" in bulletin
    assert "/sources/#" not in badge + bulletin
