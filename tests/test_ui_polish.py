from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_daily_display_heading_is_separate_from_seo_title() -> None:
    page = read("src/pages/daily/[date].astro")
    articles = read("src/lib/articles.ts")

    assert "const seoTitle = dailyTitle(date, articles)" in page
    assert "const displayTitle = dailyDisplayTitle(date, articles.length)" in page
    assert "title={seoTitle}" in page
    assert "name: seoTitle" in page
    assert "<h1>{displayTitle}</h1>" in page
    assert "export function dailyDisplayTitle" in articles


def test_ui_uses_japanese_dates_and_editorial_archive_layout() -> None:
    site = read("src/lib/site.ts")
    index = read("src/pages/index.astro")
    archive = read("src/pages/archive.astro")

    assert "month: 'long'" in site
    assert "formatJapaneseMonth" in site
    assert "formatJapaneseDate(latestDate)" in index
    assert "formatJapaneseDate(date)" in index
    assert "formatJapaneseMonth(month)" in archive
    assert 'class="archive-list__content"' in archive


def test_navigation_and_internal_ctas_have_shared_visual_states() -> None:
    layout = read("src/layouts/BaseLayout.astro")
    index = read("src/pages/index.astro")
    styles = read("src/styles/global.css")

    assert "aria-current={item.active ? 'page' : undefined}" in layout
    assert "a[aria-current='page']" in styles
    assert "min-block-size: 44px" in styles
    assert index.count('class="internal-cta"') == 2


def test_daily_navigation_separates_previous_and_next_dates() -> None:
    page = read("src/pages/daily/[date].astro")
    styles = read("src/styles/global.css")

    assert "前のダイジェスト" in page
    assert "次のダイジェスト" in page
    assert 'class="date-navigation__link date-navigation__link--next"' in page
    assert ".date-navigation {" in styles
    assert "grid-template-columns: repeat(2, minmax(0, 1fr));" in styles
    assert ".date-navigation__link {" in styles
    assert "min-block-size: 44px;" in styles


def test_cards_and_digest_cells_use_stable_visual_rhythm() -> None:
    global_styles = read("src/styles/global.css")
    refinements = read("src/styles/refinement.css")

    assert ".news-card {\n  align-items: stretch;" in refinements
    assert "align-self: stretch;" in refinements
    assert "clamp(16rem, 32%, 24rem)" in refinements
    assert "min-height: calc(1.4em * 2)" in global_styles
    assert "min-height: calc(1.7em * 2)" in global_styles
    assert "-webkit-line-clamp: 2" in global_styles
    assert "align-self: end" in global_styles


def test_article_images_are_not_cropped_and_caption_is_right_aligned() -> None:
    article = read("src/pages/articles/[year]/[month]/[day]/[slug].astro")
    refinements = read("src/styles/refinement.css")

    assert "defaultNewsImagePath(data.articleId)" in article
    assert "object-fit: contain" in refinements
    assert "text-align: right" in refinements
    assert "aspect-ratio: 16 / 7" not in refinements


def test_default_image_variants_are_small_webp_assets() -> None:
    site = read("src/lib/site.ts")

    assert "seed.match(/[0-9a-f]{8}$/i)" in site
    for index in range(1, 11):
        name = f"default-news-image-{index}.webp"
        path = ROOT / "public" / name
        assert f"'/{name}'" in site
        assert path.exists()
        assert path.read_bytes().startswith(b"RIFF")
        assert path.stat().st_size < 100_000


def test_consecutive_card_images_use_deduplicated_selection() -> None:
    site = read("src/lib/site.ts")
    card = read("src/components/NewsCard.astro")

    assert "export function selectSequentialNewsCardImages" in site
    assert "if (src === previousSrc)" in site
    assert "defaultNewsImagePath(item.articleId, previousSrc)" in site
    assert "imageSource?: string" in card
    assert "imageIsSource?: boolean" in card
    assert "resolvedImageIsSource &&" in card

    list_pages = [
        read("src/pages/index.astro"),
        read("src/pages/daily/[date].astro"),
        read("src/pages/sources/[sourceId].astro"),
    ]
    for page in list_pages:
        assert "selectSequentialNewsCardImages" in page
        assert "imageSource={" in page
        assert "imageIsSource={" in page


def test_favicon_uses_the_a_mark() -> None:
    favicon = read("public/favicon.svg")

    assert ">A</text>" in favicon
    assert ">外</text>" not in favicon
