from __future__ import annotations

import argparse
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.translation_benchmark import (
    load_benchmark_config,
    run_benchmark,
    write_results,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Compare local English-to-Japanese translators")
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("config/translation_benchmark.yml"),
        help="Benchmark metadata YAML",
    )
    parser.add_argument(
        "--candidate",
        action="append",
        dest="candidates",
        help="Candidate ID; repeat to select a subset (default: all)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        help="Output directory (default: config value)",
    )
    parser.add_argument(
        "--allow-model-download",
        action="store_true",
        help="Permit explicit local model/package downloads; never used by CI or daily workflow",
    )
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    config_path = (root / args.config).resolve() if not args.config.is_absolute() else args.config
    config = load_benchmark_config(config_path, root)
    result = run_benchmark(
        config,
        candidate_ids=tuple(args.candidates or ()),
        allow_download=args.allow_model_download,
    )
    output_dir = args.output_dir or config.results_directory
    if not output_dir.is_absolute():
        output_dir = root / output_dir
    paths = write_results(result, output_dir)
    for path in paths:
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
