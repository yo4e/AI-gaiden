from pathlib import Path

from scripts.validate_rss import (
    RssValidationError,
    validate_rss,
)


ARTICLE_URL = 'https://example.pages.dev/articles/2026/08/05/example-ai-1234abcd/'


def _write_feed(
    tmp_path: Path,
    *,
    source_type: str = 'rss',
    source_element: str = '<source url="https://example.com/feed.xml">Example AI</source>',
) -> Path:
    feed = tmp_path / 'feed.xml'
    feed.write_text(
        f'''<?xml version="1.0"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom" xmlns:gaiden="https://github.com/yo4e/AI-gaiden/ns/rss">
  <channel>
    <title>AI外電</title>
    <link>https://example.pages.dev/</link>
    <item>
      <title>日本語短報</title>
      <link>{ARTICLE_URL}</link>
      <guid isPermaLink="true">{ARTICLE_URL}</guid>
      <description>AI外電が作成した短い日本語短報です。</description>
      <pubDate>Wed, 05 Aug 2026 00:00:00 GMT</pubDate>
      <atom:updated>2026-08-05T09:00:00+09:00</atom:updated>
      <gaiden:sourceType>{source_type}</gaiden:sourceType>
      <gaiden:translationStatus>complete</gaiden:translationStatus>
      <category>Example AI</category>
      {source_element}
    </item>
  </channel>
</rss>
''',
        encoding='utf-8',
    )
    return feed


def test_generated_rss_contract_fixture(tmp_path: Path) -> None:
    feed = _write_feed(tmp_path)
    sitemap = tmp_path / 'sitemap.xml'
    article = tmp_path / 'articles/2026/08/05/example-ai-1234abcd/index.html'
    article.parent.mkdir(parents=True)
    article.write_text(
        f'<link rel="canonical" href="{ARTICLE_URL}">',
        encoding='utf-8',
    )
    sitemap.write_text(
        f'''<?xml version="1.0"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>{ARTICLE_URL}</loc></url>
</urlset>
''',
        encoding='utf-8',
    )

    assert validate_rss(feed, sitemap, tmp_path) == 1


def test_github_releases_item_allows_missing_source_element(tmp_path: Path) -> None:
    feed = _write_feed(tmp_path, source_type='github_releases', source_element='')

    assert validate_rss(feed) == 1


def test_rss_item_still_requires_source_element(tmp_path: Path) -> None:
    feed = _write_feed(tmp_path, source_type='rss', source_element='')

    try:
        validate_rss(feed)
    except RssValidationError as exc:
        assert 'missing source attribution' in str(exc)
    else:
        raise AssertionError('RSS source omission must fail validation')


def test_github_releases_item_rejects_rest_api_source_element(tmp_path: Path) -> None:
    feed = _write_feed(
        tmp_path,
        source_type='github_releases',
        source_element=(
            '<source url="https://api.github.com/repos/langchain-ai/langchain/releases">'
            'LangChain Releases</source>'
        ),
    )

    try:
        validate_rss(feed)
    except RssValidationError as exc:
        assert 'must not contain source attribution' in str(exc)
    else:
        raise AssertionError('GitHub Releases source attribution must fail validation')
