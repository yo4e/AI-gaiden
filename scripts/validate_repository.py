from __future__ import annotations

import re
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.content_writer import article_id_for, validate_article_data  # noqa: E402
from scripts.utils import load_feed_configs, parse_frontmatter  # noqa: E402


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
    source_ids = set(re.findall(r"\bid:\s*'([a-z0-9-]+)'", source_text))
    configured_ids = {config.id for config in configs}
    if source_ids != configured_ids:
        raise ValueError(
            "config/feeds.yml and src/data/sources.ts source IDs differ: "
            f"feeds={sorted(configured_ids)} site={sorted(source_ids)}"
        )
    print(
        f"Validated {len(configs)} feed configs, {article_count} article files, "
        f"{len(dedupe_keys)} unique dedupe keys"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
