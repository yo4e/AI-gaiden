from __future__ import annotations

import re
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.content_writer import article_id_for, validate_article_data  # noqa: E402
from scripts.translation_benchmark import validate_benchmark_assets  # noqa: E402
from scripts.utils import load_feed_configs, parse_frontmatter  # noqa: E402

SOURCE_OBJECT_RE = re.compile(r"  \{\n(?P<body>.*?)\n  \},", re.DOTALL)


def _source_string(body: str, field: str) -> str:
    match = re.search(rf"^\s*{re.escape(field)}:\s*'([^']*)',?\s*$", body, re.MULTILINE)
    if not match:
        raise ValueError(f"src/data/sources.ts is missing source field: {field}")
    return match.group(1)


def parse_site_sources(source_text: str) -> dict[str, dict[str, object]]:
    """Parse the static source catalog used by the Astro site."""
    parsed: dict[str, dict[str, object]] = {}
    for match in SOURCE_OBJECT_RE.finditer(source_text):
        body = match.group("body")
        source_id = _source_string(body, "id")
        if source_id in parsed:
            raise ValueError(f"Duplicate source ID in src/data/sources.ts: {source_id}")
        enabled_match = re.search(r"^\s*enabled:\s*(true|false),?\s*$", body, re.MULTILINE)
        if not enabled_match:
            raise ValueError(f"src/data/sources.ts is missing source field: enabled ({source_id})")
        categories_match = re.search(
            r"^\s*categories:\s*\[([^]]*)\],?\s*$", body, re.MULTILINE
        )
        if not categories_match:
            raise ValueError(
                f"src/data/sources.ts is missing source field: categories ({source_id})"
            )
        parsed[source_id] = {
            "id": source_id,
            "name": _source_string(body, "name"),
            "homepage": _source_string(body, "homepage"),
            "url": _source_string(body, "feedUrl"),
            "enabled": enabled_match.group(1) == "true",
            "categories": tuple(re.findall(r"'([^']*)'", categories_match.group(1))),
            "image_policy": _source_string(body, "imagePolicy"),
        }
    if not parsed:
        raise ValueError("No source objects found in src/data/sources.ts")
    return parsed


def validate_source_consistency(configs: list, source_text: str) -> int:
    """Ensure the Astro source catalog mirrors the feed configuration metadata."""
    site_sources = parse_site_sources(source_text)
    config_by_id = {config.id: config for config in configs}
    if set(site_sources) != set(config_by_id):
        raise ValueError(
            "config/feeds.yml and src/data/sources.ts source IDs differ: "
            f"feeds={sorted(config_by_id)} site={sorted(site_sources)}"
        )
    for source_id, config in config_by_id.items():
        expected = {
            "id": config.id,
            "name": config.name,
            "homepage": config.homepage,
            "url": config.url,
            "enabled": config.enabled,
            "categories": config.categories,
            "image_policy": config.image_policy,
        }
        actual = site_sources[source_id]
        if actual != expected:
            raise ValueError(
                f"Source metadata differs for {source_id}: feeds={expected} site={actual}"
            )
    return len(site_sources)


def validate_articles(content_dir: Path, configs: list) -> tuple[int, set[str], set[str]]:
    """Validate article files against all configured sources, including disabled ones."""
    if not content_dir.exists():
        raise ValueError("src/content/articles must exist")
    configured_ids = {config.id for config in configs}
    article_count = 0
    dedupe_keys: set[str] = set()
    article_ids: set[str] = set()
    for path in sorted(content_dir.rglob("*.md")):
        data = parse_frontmatter(path)
        validate_article_data(data)
        expected_path = content_dir / str(data["dateJst"]) / f"{data['articleId']}.md"
        if path != expected_path:
            raise ValueError(f"Article path does not match dateJst/articleId: {path}")
        if data["dedupeKey"] in dedupe_keys:
            raise ValueError(f"Duplicate dedupeKey: {data['dedupeKey']}")
        if data["articleId"] in article_ids:
            raise ValueError(f"Duplicate articleId: {data['articleId']}")
        if data["articleId"] != article_id_for(data["sourceId"], data["dedupeKey"]):
            raise ValueError(f"articleId is not deterministic: {path}")
        if data["sourceId"] not in configured_ids:
            raise ValueError(f"Article references an unknown source: {path}")
        dedupe_keys.add(data["dedupeKey"])
        article_ids.add(data["articleId"])
        article_count += 1
    return article_count, dedupe_keys, article_ids


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    configs = load_feed_configs(root / "config/feeds.yml")
    if not any(config.enabled for config in configs):
        raise ValueError("At least one official feed must be enabled")

    content_dir = root / "src/content/articles"
    article_count, dedupe_keys, article_ids = validate_articles(content_dir, configs)

    legacy_dir = root / "src/content/daily"
    if legacy_dir.exists() and any(legacy_dir.glob("*.md")):
        raise ValueError("Legacy daily Markdown files remain after article migration")

    source_text = (root / "src/data/sources.ts").read_text(encoding="utf-8")
    source_count = validate_source_consistency(configs, source_text)
    benchmark_corpus_count, benchmark_candidate_count = validate_benchmark_assets(root)
    print(
        f"Validated {len(configs)} feed configs and {source_count} site sources, "
        f"{article_count} article files, "
        f"{len(dedupe_keys)} unique dedupe keys, "
        f"{benchmark_corpus_count} benchmark items and "
        f"{benchmark_candidate_count} translation candidates"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
