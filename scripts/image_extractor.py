from __future__ import annotations

from typing import Any

from bs4 import BeautifulSoup

from scripts.utils import is_http_url


def _first_url(candidates: list[str | None]) -> str | None:
    for candidate in candidates:
        if candidate and is_http_url(candidate):
            return candidate.strip()
    return None


def extract_rss_image(entry: Any) -> tuple[str | None, str | None]:
    """Extract an image only from fields present in the RSS/Atom entry."""
    thumbnails = entry.get("media_thumbnail", []) or []
    image = _first_url(
        [value.get("url") for value in thumbnails if isinstance(value, dict)]
    )
    if image:
        return image, _extract_license(entry)

    media_content = entry.get("media_content", []) or []
    media_candidates = []
    for value in media_content:
        if not isinstance(value, dict):
            continue
        media_type = str(value.get("type", ""))
        medium = str(value.get("medium", ""))
        if media_type.startswith("image/") or medium == "image":
            media_candidates.append(value.get("url"))
    image = _first_url(media_candidates)
    if image:
        return image, _extract_license(entry)

    enclosures = entry.get("enclosures", []) or []
    enclosure_candidates = []
    for value in enclosures:
        if not isinstance(value, dict):
            continue
        if str(value.get("type", "")).startswith("image/"):
            enclosure_candidates.append(value.get("href") or value.get("url"))
    image = _first_url(enclosure_candidates)
    if image:
        return image, _extract_license(entry)

    summary_html = entry.get("summary") or entry.get("description") or ""
    soup = BeautifulSoup(str(summary_html), "html.parser")
    image_element = soup.find("img")
    image = _first_url([image_element.get("src") if image_element else None])
    return image, _extract_license(entry) if image else None


def _extract_license(entry: Any) -> str | None:
    for key in ("media_license", "license", "rights"):
        value = entry.get(key)
        if isinstance(value, dict):
            value = value.get("content") or value.get("href")
        if value:
            text = str(value).strip()
            return text[:300] if text else None
    return None
