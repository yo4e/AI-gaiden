from __future__ import annotations

import re
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.content_writer import validate_daily_data  # noqa: E402
from scripts.utils import load_feed_configs, parse_frontmatter  # noqa: E402


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    configs = load_feed_configs(root / "config/feeds.yml")
    if not any(config.enabled for config in configs):
        raise ValueError("At least one official feed must be enabled")
    content_dir = root / "src/content/daily"
    for path in content_dir.glob("*.md"):
        validate_daily_data(parse_frontmatter(path))
    source_text = (root / "src/data/sources.ts").read_text(encoding="utf-8")
    source_ids = set(re.findall(r"\bid:\s*'([a-z0-9-]+)'", source_text))
    configured_ids = {config.id for config in configs}
    if source_ids != configured_ids:
        raise ValueError(
            "config/feeds.yml and src/data/sources.ts source IDs differ: "
            f"feeds={sorted(configured_ids)} site={sorted(source_ids)}"
        )
    print(f"Validated {len(configs)} feed configs and repository content schema")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
