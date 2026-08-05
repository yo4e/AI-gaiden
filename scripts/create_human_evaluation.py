from __future__ import annotations

import argparse
import csv
import json
import random
import sys
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.translation_benchmark import load_corpus

BLINDED_KEYS = ("A", "B", "C", "D")
SCORE_FIELDS = (
    "meaning_accuracy",
    "naturalness",
    "heading_clarity",
    "number_proper_noun_retention",
    "added_facts",
)


def _select_items(items: tuple[Any, ...], count: int) -> tuple[Any, ...]:
    if not 10 <= count <= 15:
        raise ValueError("sample count must be between 10 and 15")
    ordered = sorted(items, key=lambda item: (item.source_id, item.id))
    if count >= len(ordered):
        return ordered
    indices = {round(index * (len(ordered) - 1) / (count - 1)) for index in range(count)}
    selected = [ordered[index] for index in sorted(indices)]
    if len(selected) != count:
        selected = ordered[:count]
    return tuple(selected)


def _result_run_map(result: dict[str, Any]) -> dict[tuple[str, str, str], dict[str, Any]]:
    return {
        (row["candidate_id"], row["item_id"], row["target_type"]): row
        for row in result["runs"]
    }


def _write_samples_csv(rows: list[dict[str, Any]], path: Path) -> None:
    fieldnames = (
        "sample_id",
        "item_id",
        "target_type",
        "source_name",
        "source_url",
        "source_text",
        "blinded_key",
        "translation",
        "status",
        *SCORE_FIELDS,
        "evaluator_notes",
    )
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _write_samples_markdown(rows: list[dict[str, Any]], path: Path) -> None:
    lines = [
        "# Blinded human evaluation samples",
        "",
        "Model identities are intentionally omitted. Complete the blank "
        "evaluation columns before opening `model_key.csv`.",
        "",
    ]
    for (sample_id, target_type), group in _group_rows(rows):
        first = group[0]
        lines.extend(
            [
                f"## {sample_id} ({target_type})",
                "",
                f"- Item: `{first['item_id']}`",
                f"- Source: {first['source_name']} — <{first['source_url']}>",
                f"- Original: {first['source_text']}",
                "",
                "| Key | Translation | Meaning | Naturalness | Heading clarity | "
                "Number/name retention | Added facts | Notes |",
                "| --- | --- | ---: | ---: | ---: | ---: | --- | --- |",
            ]
        )
        for row in group:
            lines.append(
                f"| {row['blinded_key']} | {row['translation']} |  |  |  |  |  |  |"
            )
        lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def _group_rows(
    rows: list[dict[str, Any]],
) -> list[tuple[tuple[str, str], list[dict[str, Any]]]]:
    groups: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for row in rows:
        key = (row["sample_id"], row["target_type"])
        groups.setdefault(key, []).append(row)
    return list(groups.items())


def create_evaluation_files(
    result_path: Path,
    corpus_path: Path,
    output_directory: Path,
    *,
    sample_count: int = 12,
    seed: str = "issue16-2026-08-05",
) -> tuple[Path, Path, Path]:
    result = json.loads(result_path.read_text(encoding="utf-8"))
    items = _select_items(load_corpus(corpus_path), sample_count)
    candidates = list(result["candidates"])
    if len(candidates) != len(BLINDED_KEYS):
        raise ValueError("Human evaluation requires exactly four benchmark candidates")
    candidate_ids = [candidate["id"] for candidate in candidates]
    random.Random(seed).shuffle(candidate_ids)
    key_by_candidate = dict(zip(candidate_ids, BLINDED_KEYS, strict=True))
    runs = _result_run_map(result)
    rows: list[dict[str, Any]] = []
    for index, item in enumerate(items, start=1):
        sample_id = f"S{index:02d}"
        for target_type, source_text in (
            ("title", item.title_en),
            ("summary", item.summary_en),
        ):
            for candidate_id in candidate_ids:
                run = runs[(candidate_id, item.id, target_type)]
                rows.append(
                    {
                        "sample_id": sample_id,
                        "item_id": item.id,
                        "target_type": target_type,
                        "source_name": item.source_name,
                        "source_url": item.source_url,
                        "source_text": source_text,
                        "blinded_key": key_by_candidate[candidate_id],
                        "translation": run["translated_text"],
                        "status": run["status"],
                        **{field: "" for field in SCORE_FIELDS},
                        "evaluator_notes": "",
                    }
                )
    output_directory.mkdir(parents=True, exist_ok=True)
    samples_csv = output_directory / "representative_samples.csv"
    samples_md = output_directory / "representative_samples.md"
    model_key = output_directory / "model_key.csv"
    _write_samples_csv(rows, samples_csv)
    _write_samples_markdown(rows, samples_md)
    with model_key.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=("blinded_key", "candidate_id", "label", "model_revision"),
            lineterminator="\n",
        )
        writer.writeheader()
        revisions = {
            row["candidate_id"]: row["model_revision"]
            for row in result["candidate_measurements"]
        }
        for candidate_id in candidate_ids:
            candidate = next(item for item in candidates if item["id"] == candidate_id)
            writer.writerow(
                {
                    "blinded_key": key_by_candidate[candidate_id],
                    "candidate_id": candidate_id,
                    "label": candidate["label"],
                    "model_revision": revisions.get(candidate_id, "unknown"),
                }
            )
    return samples_csv, samples_md, model_key


def main() -> int:
    parser = argparse.ArgumentParser(description="Create blinded human translation samples")
    parser.add_argument(
        "--results",
        type=Path,
        default=Path("data/translation_benchmark/results/translation-benchmark.json"),
    )
    parser.add_argument(
        "--corpus",
        type=Path,
        default=Path("data/translation_benchmark/corpus.jsonl"),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/translation_benchmark/human_evaluation"),
    )
    parser.add_argument("--sample-count", type=int, default=12)
    parser.add_argument("--seed", default="issue16-2026-08-05")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    def resolve(path: Path) -> Path:
        return path if path.is_absolute() else root / path
    for path in create_evaluation_files(
        resolve(args.results),
        resolve(args.corpus),
        resolve(args.output_dir),
        sample_count=args.sample_count,
        seed=args.seed,
    ):
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
