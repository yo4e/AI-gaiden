"""Correct legacy release templates locally; dry-run by default, preserve human edits."""

from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.content_writer import render_article_markdown, validate_article_data  # noqa: E402
from scripts.utils import load_feed_configs, parse_frontmatter  # noqa: E402

REPLACEMENTS = {
    "を公式フィードで発表しました。": "を公式GitHub Releasesで発表しました。",
    "公式RSSによると、": "公式リリースによると、",
    "の公式RSSをもとにした日本語短報です。": "の公式GitHub Releasesをもとにした日本語短報です。",
}


def correct_article(data: dict, *, updated_at: str) -> dict:
    result = data.copy()
    for field in ("briefJa", "description", "excerptJa"):
        value = result[field]
        for before, after in REPLACEMENTS.items():
            value = value.replace(before, after)
        maximum = {"briefJa": 320, "description": 160, "excerptJa": 120}[field]
        if len(value) > maximum:
            disclosure = "内容は自動翻訳・定型編集されています。"
            if field == "briefJa" and disclosure in value:
                lead, _, tail = value.partition(disclosure)
                suffix = disclosure + tail
                value = lead[: maximum - len(suffix) - 1].rstrip("…。") + "…" + suffix
            else:
                value = value[: maximum - 1].rstrip("…。") + "…"
        result[field] = value
    if result != data:
        result["updatedAt"] = updated_at
        result["correctionHistory"] = [
            *data.get("correctionHistory", []),
            {
                "date": updated_at,
                "description": "取得元の表記をRSSからGitHub Releasesに訂正しました。",
            },
        ]
        validate_article_data(result)
    return result


def correct_releases(
    content_dir: Path, feeds: Path, *, updated_at: str, apply: bool
) -> tuple[int, int]:
    if datetime.fromisoformat(updated_at.replace("Z", "+00:00")).tzinfo is None:
        raise ValueError("--updated-at must be an ISO timestamp with timezone")
    release_ids = {c.id for c in load_feed_configs(feeds) if c.source_type == "github_releases"}
    changes: list[tuple[Path, str]] = []
    skipped = 0
    for path in sorted(content_dir.rglob("*.md")):
        data = parse_frontmatter(path)
        if data.get("sourceId") not in release_ids:
            continue
        body = path.read_text(encoding="utf-8").split("---", 2)[-1].strip()
        if data.get("humanEdited") or data.get("correctionHistory") or body:
            skipped += 1
            print(f"Protected (unchanged): {path}")
            continue
        revised = correct_article(data, updated_at=updated_at)
        if revised != data:
            # Validate all candidates before writing any of them.
            changes.append((path, render_article_markdown(revised)))
    for path, markdown in changes:
        print(f"{'Correct' if apply else 'Would correct'}: {path}")
        if apply:
            path.write_text(markdown, encoding="utf-8")
    print(f"Candidates: {len(changes)}; protected: {skipped}; applied: {apply}")
    return len(changes), skipped


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--content-dir", type=Path, default=Path("src/content/articles"))
    parser.add_argument("--feeds", type=Path, default=Path("config/feeds.yml"))
    parser.add_argument("--updated-at", required=True)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    correct_releases(args.content_dir, args.feeds, updated_at=args.updated_at, apply=args.apply)


if __name__ == "__main__":
    main()
