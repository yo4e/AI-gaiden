from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.translator import TranslationError  # noqa: E402
from scripts.updater import UpdateError, run_update  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Update AI外電 from configured official feeds")
    parser.add_argument("--config", type=Path, default=Path("config/feeds.yml"))
    parser.add_argument("--seen", type=Path, default=Path("data/seen.json"))
    parser.add_argument("--content-dir", type=Path, default=Path("src/content/articles"))
    parser.add_argument("--cache", type=Path, default=Path(".cache/feed-state.json"))
    parser.add_argument(
        "--bootstrap-days",
        type=int,
        default=int(os.environ.get("BOOTSTRAP_DAYS", "3")),
        help="Lookback window in days (1-7)",
    )
    return parser.parse_args()


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    logging.getLogger("argostranslate").setLevel(logging.WARNING)
    logging.getLogger("stanza").setLevel(logging.WARNING)
    args = parse_args()
    try:
        count = run_update(
            config_path=args.config,
            seen_path=args.seen,
            content_dir=args.content_dir,
            cache_path=args.cache,
            bootstrap_days=args.bootstrap_days,
        )
    except (UpdateError, TranslationError, ValueError) as exc:
        logging.error("Update stopped safely: %s", exc)
        return 1
    logging.info("Update complete: %d new item(s)", count)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
