"""One-time conversion of legacy daily item arrays into article Markdown files."""

from __future__ import annotations

import argparse
import logging
import sys
from datetime import UTC, datetime
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.content_writer import (  # noqa: E402
    article_data_from_item,
    article_relative_path,
    render_article_markdown,
)
from scripts.models import PreparedItem  # noqa: E402
from scripts.utils import load_feed_configs, parse_feed_datetime, parse_frontmatter  # noqa: E402

LOGGER = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Migrate legacy daily item arrays to articles")
    parser.add_argument("--source-dir", type=Path, default=Path("src/content/daily"))
    parser.add_argument("--output-dir", type=Path, default=Path("src/content/articles"))
    parser.add_argument("--feeds", type=Path, default=Path("config/feeds.yml"))
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing migration output (use only before the first commit)",
    )
    return parser.parse_args()


def migrate(
    source_dir: Path, output_dir: Path, feeds_path: Path, *, overwrite: bool = False
) -> int:
    configs = {config.id: config for config in load_feed_configs(feeds_path)}
    migrated = 0
    seen_paths: set[Path] = set()
    for daily_path in sorted(source_dir.glob("*.md")):
        daily_data = parse_frontmatter(daily_path)
        generated_at = parse_feed_datetime(str(daily_data.get("updatedAt"))) or datetime.now(UTC)
        for raw in daily_data.get("items", []):
            if not isinstance(raw, dict):
                raise ValueError(f"Invalid item in {daily_path}")
            published_at = parse_feed_datetime(str(raw.get("publishedAt")))
            if not published_at:
                raise ValueError(f"Item has no usable publishedAt in {daily_path}")
            source_id = str(raw["sourceId"])
            item = PreparedItem(
                source_id=source_id,
                source_name=str(raw["sourceName"]),
                title_ja=str(raw["titleJa"]),
                title_original=str(raw["titleOriginal"]),
                brief_ja=str(raw["briefJa"]),
                url=str(raw["url"]),
                canonical_url=str(raw["url"]),
                published_at=published_at,
                image_url=raw.get("imageUrl"),
                image_license=raw.get("imageLicense"),
                author=raw.get("author"),
                translation_status=str(raw.get("translationStatus", "partial")),
                dedupe_key=str(raw["dedupeKey"]),
                source_homepage=configs.get(source_id).homepage if source_id in configs else None,
                fetched_at=generated_at,
            )
            data = article_data_from_item(
                item,
                generated_at=generated_at,
                generated_iso=generated_at.astimezone().isoformat(timespec="seconds"),
                created_iso=generated_at.astimezone().isoformat(timespec="seconds"),
            )
            relative_path = article_relative_path(data["dateJst"], data["articleId"])
            if relative_path in seen_paths:
                raise ValueError(f"Article path collision in migration batch: {relative_path}")
            seen_paths.add(relative_path)
            destination = output_dir / relative_path
            if destination.exists() and not overwrite:
                existing = parse_frontmatter(destination)
                if existing.get("dedupeKey") != data["dedupeKey"]:
                    raise ValueError(f"Article ID collision: {destination}")
                continue
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(render_article_markdown(data), encoding="utf-8")
            migrated += 1
    return migrated


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    args = parse_args()
    count = migrate(args.source_dir, args.output_dir, args.feeds, overwrite=args.overwrite)
    LOGGER.info("Migrated %d article(s)", count)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
