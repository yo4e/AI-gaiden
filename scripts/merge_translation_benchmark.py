"""Combine per-candidate local benchmark snapshots without changing site data."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.translation_benchmark import (
    TranslationFidelity,
    load_benchmark_config,
    load_corpus,
    write_results,
)


def _unavailable_rows(candidate_id: str, reason: str, corpus_path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item in load_corpus(corpus_path):
        for target_type in ("title", "summary"):
            rows.append(
                {
                    "candidate_id": candidate_id,
                    "target_type": target_type,
                    "item_id": item.id,
                    "status": "unavailable",
                    "translated_text": "",
                    "quality_passed": False,
                    "quality_reasons": [reason],
                    "elapsed_ms": None,
                    "peak_memory_mb": None,
                    **TranslationFidelity(0, 0, 0, 0, 0, 0).as_dict(),
                }
            )
    return rows


def _unavailable_aggregates(candidate_id: str) -> list[dict[str, Any]]:
    return [
        {
            "candidate_id": candidate_id,
            "target_type": target_type,
            "items": 40,
            "available": 0,
            "quality_passed": 0,
            "quality_rejected": 0,
            "average_elapsed_ms": None,
            "numbers_total": 0,
            "numbers_preserved": 0,
            "urls_total": 0,
            "urls_preserved": 0,
            "proper_nouns_total": 0,
            "proper_nouns_preserved": 0,
        }
        for target_type in ("title", "summary")
    ]


def merge_results(
    config_path: Path,
    result_paths: tuple[Path, ...],
    unavailable_id: str,
    unavailable_reason: str,
) -> dict[str, Any]:
    root = config_path.parents[1]
    config = load_benchmark_config(config_path, root)
    snapshots = [json.loads(path.read_text(encoding="utf-8")) for path in result_paths]
    if not snapshots:
        raise ValueError("At least one successful candidate result is required")
    expected = {
        "version": config.version,
        "corpus_sha256": snapshots[0]["corpus_sha256"],
        "glossary_sha256": snapshots[0]["glossary_sha256"],
        "conditions": snapshots[0]["conditions"],
    }
    candidates_by_id = {candidate.id: candidate for candidate in config.candidates}
    by_id = {snapshot["candidates"][0]["id"]: snapshot for snapshot in snapshots}
    if unavailable_id in by_id:
        raise ValueError(f"Unavailable candidate also has a successful snapshot: {unavailable_id}")
    if unavailable_id not in candidates_by_id:
        raise ValueError(f"Unknown unavailable candidate: {unavailable_id}")
    for snapshot in snapshots:
        if any(snapshot[key] != value for key, value in expected.items()):
            raise ValueError("Candidate snapshots do not share corpus, glossary, or conditions")
    if set(by_id) | {unavailable_id} != set(candidates_by_id):
        missing = sorted(set(candidates_by_id) - set(by_id) - {unavailable_id})
        raise ValueError(f"Missing candidate snapshots: {', '.join(missing)}")

    result: dict[str, Any] = {
        "version": config.version,
        "corpus_sha256": expected["corpus_sha256"],
        "glossary_sha256": expected["glossary_sha256"],
        "conditions": expected["conditions"],
        "runtime": {
            **snapshots[0]["runtime"],
            "measurement_note": (
                "Successful candidates were measured in separate local runs and combined; "
                "environment metadata is shared across this snapshot."
            ),
        },
        "candidates": [candidate.as_dict() for candidate in config.candidates],
        "candidate_measurements": [],
        "runs": [],
        "aggregates": [],
    }
    for candidate in config.candidates:
        if candidate.id == unavailable_id:
            result["candidate_measurements"].append(
                {
                    "candidate_id": candidate.id,
                    "status": "unavailable",
                    "failure_reason": unavailable_reason,
                    "model_revision": "unknown",
                    "setup_elapsed_ms": None,
                    "initial_acquisition_time_ms": None,
                    "initial_acquisition_scope": "not_measured",
                    "inference_time_ms_total": None,
                    "inference_time_ms_average": None,
                    "peak_memory_mb": None,
                    "cache_bytes_before": None,
                    "cache_bytes_after": None,
                    "cache_bytes_delta": None,
                    "cache_measurement_scope": "not_measured",
                    "memory_measurement_scope": "not_measured",
                }
            )
            result["runs"].extend(
                _unavailable_rows(candidate.id, unavailable_reason, config.corpus_path)
            )
            result["aggregates"].extend(_unavailable_aggregates(candidate.id))
            continue
        snapshot = by_id[candidate.id]
        result["candidate_measurements"].extend(snapshot["candidate_measurements"])
        result["runs"].extend(snapshot["runs"])
        result["aggregates"].extend(snapshot["aggregates"])
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Merge isolated translation benchmark runs")
    parser.add_argument("--config", type=Path, default=Path("config/translation_benchmark.yml"))
    parser.add_argument("--result", type=Path, action="append", required=True)
    parser.add_argument("--unavailable-id", required=True)
    parser.add_argument("--unavailable-reason", required=True)
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    config_path = args.config if args.config.is_absolute() else root / args.config
    result_paths = tuple(path if path.is_absolute() else root / path for path in args.result)
    result = merge_results(
        config_path,
        result_paths,
        args.unavailable_id,
        args.unavailable_reason,
    )
    config = load_benchmark_config(config_path, root)
    output_directory = args.output_dir or config.results_directory
    if not output_directory.is_absolute():
        output_directory = root / output_directory
    for path in write_results(result, output_directory):
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
