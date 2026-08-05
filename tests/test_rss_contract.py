from pathlib import Path

from scripts.validate_rss import validate_rss


def test_generated_rss_contract_fixture(tmp_path: Path) -> None:
    feed = tmp_path / 'feed.xml'
    sitemap = tmp_path / 'sitemap.xml'
    article = tmp_path / 'articles/2026/08/05/example-ai-1234abcd/index.html'
    article.parent.mkdir(parents=True)
    article.write_text(
        '<link rel="canonical" href="https://example.pages.dev/articles/2026/08/05/example-ai-1234abcd/">',
        encoding='utf-8',
    )
    feed.write_text(
        '''<?xml version="1.0"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom" xmlns:gaiden="https://github.com/yo4e/AI-gaiden/ns/rss">
  <channel>
    <title>AI外電</title>
    <link>https://example.pages.dev/</link>
    <item>
      <title>日本語短報</title>
      <link>https://example.pages.dev/articles/2026/08/05/example-ai-1234abcd/</link>
      <guid isPermaLink="true">https://example.pages.dev/articles/2026/08/05/example-ai-1234abcd/</guid>
      <description>AI外電が作成した短い日本語短報です。</description>
      <pubDate>Wed, 05 Aug 2026 00:00:00 GMT</pubDate>
      <atom:updated>2026-08-05T09:00:00+09:00</atom:updated>
      <gaiden:translationStatus>complete</gaiden:translationStatus>
      <category>Example AI</category>
      <source url="https://example.com/feed.xml">Example AI</source>
    </item>
  </channel>
</rss>
''',
        encoding='utf-8',
    )
    sitemap.write_text(
        '''<?xml version="1.0"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>https://example.pages.dev/articles/2026/08/05/example-ai-1234abcd/</loc></url>
</urlset>
''',
        encoding='utf-8',
    )

    assert validate_rss(feed, sitemap, tmp_path) == 1
