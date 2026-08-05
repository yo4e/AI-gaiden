from __future__ import annotations

import argparse
import re
import sys
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.parse import urlparse
from xml.etree import ElementTree


class RssValidationError(ValueError):
    """Raised when the generated site RSS violates its public contract."""


def _local_name(tag: str) -> str:
    return tag.rsplit('}', 1)[-1].rsplit(':', 1)[-1]


def _child(element: ElementTree.Element, name: str) -> ElementTree.Element | None:
    return next((child for child in element if _local_name(child.tag) == name), None)


def _text(element: ElementTree.Element, name: str) -> str:
    child = _child(element, name)
    value = ''.join(child.itertext()).strip() if child is not None else ''
    if not value:
        raise RssValidationError(f'Missing RSS {name}')
    return value


def _require_absolute_http_url(value: str, field: str) -> None:
    parsed = urlparse(value)
    if parsed.scheme not in {'http', 'https'} or not parsed.netloc:
        raise RssValidationError(f'{field} must be an absolute HTTP(S) URL: {value}')


def _sitemap_urls(path: Path) -> set[str]:
    root = ElementTree.parse(path).getroot()
    urls: set[str] = set()
    if _local_name(root.tag) == 'sitemapindex':
        for sitemap in root:
            loc = _child(sitemap, 'loc')
            if loc is None or not ''.join(loc.itertext()).strip():
                raise RssValidationError('Sitemap index contains an empty loc')
            child_path = path.parent / Path(urlparse(''.join(loc.itertext()).strip()).path).name
            if not child_path.exists():
                raise RssValidationError(f'Sitemap child does not exist: {child_path}')
            urls.update(_sitemap_urls(child_path))
        return urls
    for url in root:
        loc = _child(url, 'loc')
        if loc is not None:
            urls.add(''.join(loc.itertext()).strip())
    return urls


def validate_rss(
    feed_path: Path,
    sitemap_path: Path | None = None,
    site_root: Path | None = None,
) -> int:
    root = ElementTree.parse(feed_path).getroot()
    if _local_name(root.tag) != 'rss' or root.attrib.get('version') != '2.0':
        raise RssValidationError('Feed must be RSS 2.0')
    channel = _child(root, 'channel')
    if channel is None:
        raise RssValidationError('RSS channel is missing')
    channel_link = _text(channel, 'link')
    _require_absolute_http_url(channel_link, 'channel link')
    items = [child for child in channel if _local_name(child.tag) == 'item']
    if not items:
        raise RssValidationError('Feed must contain at least one item')

    links: set[str] = set()
    for item in items:
        link = _text(item, 'link')
        guid_element = _child(item, 'guid')
        guid = _text(item, 'guid')
        _require_absolute_http_url(link, 'item link')
        if guid != link or guid_element is None or guid_element.attrib.get('isPermaLink') != 'true':
            raise RssValidationError(f'GUID must be the stable article URL: {link}')
        if link in links:
            raise RssValidationError(f'Duplicate item link: {link}')
        links.add(link)

        description = _text(item, 'description')
        if len(description) > 320:
            raise RssValidationError(f'RSS description is too long: {link}')
        lowered = description.lower()
        if any(marker in lowered for marker in ('<img', '<iframe', '<script', '<style')):
            raise RssValidationError(f'RSS description contains embedded markup: {link}')
        if any(_local_name(child.tag) == 'encoded' for child in item):
            raise RssValidationError(f'RSS item contains content:encoded: {link}')

        published_at = _text(item, 'pubDate')
        try:
            parsedate_to_datetime(published_at)
        except (TypeError, ValueError) as exc:
            raise RssValidationError(f'Invalid RSS pubDate: {published_at}') from exc
        updated = _child(item, 'updated')
        if updated is None or not ''.join(updated.itertext()).strip():
            raise RssValidationError(f'RSS item is missing updated metadata: {link}')
        category = _child(item, 'category')
        if category is None or not ''.join(category.itertext()).strip():
            raise RssValidationError(f'RSS item is missing a source category: {link}')
        source = _child(item, 'source')
        if source is None:
            raise RssValidationError(f'RSS item is missing source attribution: {link}')
        source_url = source.attrib.get('url', '')
        _require_absolute_http_url(source_url, 'source URL')
        translation_status = next(
            (child for child in item if _local_name(child.tag) == 'translationStatus'), None
        )
        if translation_status is None or ''.join(translation_status.itertext()).strip() not in {
            'complete',
            'partial',
        }:
            raise RssValidationError(f'RSS item is missing translation status: {link}')

    if sitemap_path is not None:
        sitemap_urls = _sitemap_urls(sitemap_path)
        missing = sorted(links - sitemap_urls)
        if missing:
            raise RssValidationError(f'RSS links missing from sitemap: {missing}')
    if site_root is not None:
        for link in links:
            article_path = urlparse(link).path.strip('/')
            html_path = site_root / article_path / 'index.html'
            if not html_path.exists():
                raise RssValidationError(f'RSS article page does not exist: {html_path}')
            html = html_path.read_text(encoding='utf-8')
            canonical = re.search(
                r'<link\s+rel="canonical"\s+href="([^"]+)"', html, flags=re.IGNORECASE
            )
            if canonical is None or canonical.group(1) != link:
                raise RssValidationError(f'RSS link does not match page canonical: {link}')
        if (site_root / 'daily' / 'feed.xml').exists():
            raise RssValidationError('Daily RSS must not be generated in this phase')
    return len(items)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('feed', type=Path)
    parser.add_argument('sitemap', type=Path, nargs='?')
    parser.add_argument('site_root', type=Path, nargs='?')
    args = parser.parse_args()
    try:
        count = validate_rss(args.feed, args.sitemap, args.site_root)
    except (ElementTree.ParseError, OSError, RssValidationError) as exc:
        print(f'RSS validation failed: {exc}', file=sys.stderr)
        return 1
    print(f'Validated {count} RSS items: {args.feed}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
