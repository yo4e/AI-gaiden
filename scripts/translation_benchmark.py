"""Offline, model-independent translation comparison for Issue #16.

The normal site pipeline never imports optional Transformers dependencies or downloads
comparison models. This module is used only by the explicit local benchmark command.
"""

from __future__ import annotations

import csv
import hashlib
import json
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Protocol

import yaml

from scripts.translation_glossary import (
    GlossaryTerm,
    apply_glossary,
    load_glossary,
    protected_glossary_terms,
)
from scripts.translation_quality import (
    TranslationFidelity,
    check_translation_quality,
    translation_fidelity_metrics,
)
from scripts.translator import (
    ArgosTranslator,
    TranslationError,
    protect_translation_input,
    restore_translation_output,
    validate_translation,
)
from scripts.utils import is_http_url, load_feed_configs


class BenchmarkConfigurationError(ValueError):
    """Raised when benchmark metadata or corpus is incomplete or unsafe."""


@dataclass(frozen=True)
class BenchmarkItem:
    id: str
    source_id: str
    source_name: str
    source_url: str
    published_at: str
    title_en: str
    summary_en: str
    reference_title_ja: str
    reference_summary_ja: str
    human_title_score: int | float | None
    human_summary_score: int | float | None
    notes: str


@dataclass(frozen=True)
class BenchmarkCandidate:
    id: str
    label: str
    backend: str
    model_id: str | None
    package: str | None
    official_url: str
    model_card_url: str
    license: str
    commercial_status: str
    model_size: str
    cpu_time: str
    memory: str
    download_time: str
    cache_size: str
    actions_feasibility: str
    production_candidate: bool
    exclusion_reason: str

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class BenchmarkConfig:
    version: int
    corpus_path: Path
    glossary_path: Path
    results_directory: Path
    max_input_tokens: int
    max_new_tokens: int
    num_beams: int
    candidates: tuple[BenchmarkCandidate, ...]


class BenchmarkAdapter(Protocol):
    def translate(self, text: str) -> str:
        """Translate one English title or summary under the shared adapter contract."""


def _required_string(item: dict[str, Any], key: str, context: str) -> str:
    value = str(item.get(key, "")).strip()
    if not value:
        raise BenchmarkConfigurationError(f"{context} requires {key}")
    return value


def load_benchmark_config(path: Path, root: Path | None = None) -> BenchmarkConfig:
    root = root or path.parent.parent
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise BenchmarkConfigurationError(f"Could not read benchmark config: {exc}") from exc
    if not isinstance(raw, dict) or not isinstance(raw.get("candidates"), list):
        raise BenchmarkConfigurationError("Benchmark config must contain candidates")
    version = int(raw.get("version", 0))
    if version != 1:
        raise BenchmarkConfigurationError("Unsupported benchmark config version")
    runner = raw.get("runner")
    if not isinstance(runner, dict):
        raise BenchmarkConfigurationError("Benchmark config must contain runner settings")
    candidates: list[BenchmarkCandidate] = []
    seen: set[str] = set()
    fields = (
        "label",
        "backend",
        "official_url",
        "model_card_url",
        "license",
        "commercial_status",
        "model_size",
        "cpu_time",
        "memory",
        "download_time",
        "cache_size",
        "actions_feasibility",
        "exclusion_reason",
    )
    for index, item in enumerate(raw["candidates"]):
        if not isinstance(item, dict):
            raise BenchmarkConfigurationError(f"Candidate {index} must be a mapping")
        candidate_id = _required_string(item, "id", f"Candidate {index}")
        if candidate_id in seen:
            raise BenchmarkConfigurationError(f"Duplicate benchmark candidate: {candidate_id}")
        seen.add(candidate_id)
        values = {
            field: _required_string(item, field, candidate_id)
            for field in fields
            if field != "exclusion_reason"
        }
        values["exclusion_reason"] = str(item.get("exclusion_reason", "")).strip()
        candidates.append(
            BenchmarkCandidate(
                id=candidate_id,
                model_id=str(item["model_id"]).strip() if item.get("model_id") else None,
                package=str(item["package"]).strip() if item.get("package") else None,
                production_candidate=bool(item.get("production_candidate", False)),
                **values,
            )
        )
    try:
        corpus_path = (root / str(raw["corpus"]))
        glossary_path = (root / str(raw["glossary"]))
        results_directory = root / str(raw.get("results_directory", "artifacts/translation"))
        return BenchmarkConfig(
            version=version,
            corpus_path=corpus_path,
            glossary_path=glossary_path,
            results_directory=results_directory,
            max_input_tokens=int(runner.get("max_input_tokens", 512)),
            max_new_tokens=int(runner.get("max_new_tokens", 256)),
            num_beams=int(runner.get("num_beams", 1)),
            candidates=tuple(candidates),
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise BenchmarkConfigurationError(
            f"Invalid benchmark path or runner setting: {exc}"
        ) from exc


def _score_or_none(value: Any, context: str) -> int | float | None:
    if value is None or value == "":
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise BenchmarkConfigurationError(f"{context} human score must be null or numeric")
    return value


def load_corpus(path: Path) -> tuple[BenchmarkItem, ...]:
    items: list[BenchmarkItem] = []
    seen: set[str] = set()
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise BenchmarkConfigurationError(f"Could not read benchmark corpus: {exc}") from exc
    for line_number, line in enumerate(lines, start=1):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        try:
            raw = json.loads(line)
        except json.JSONDecodeError as exc:
            raise BenchmarkConfigurationError(f"Invalid corpus JSON on line {line_number}") from exc
        if not isinstance(raw, dict):
            raise BenchmarkConfigurationError(f"Corpus line {line_number} must be an object")
        item_id = _required_string(raw, "id", f"Corpus line {line_number}")
        if item_id in seen:
            raise BenchmarkConfigurationError(f"Duplicate corpus ID: {item_id}")
        seen.add(item_id)
        title = _required_string(raw, "title_en", item_id)
        summary = _required_string(raw, "summary_en", item_id)
        source_url = _required_string(raw, "source_url", item_id)
        if not is_http_url(source_url):
            raise BenchmarkConfigurationError(f"Corpus source_url is not HTTP(S): {item_id}")
        reference_title = str(raw.get("reference_title_ja", ""))
        reference_summary = str(raw.get("reference_summary_ja", ""))
        if reference_title or reference_summary:
            raise BenchmarkConfigurationError(f"Human references must remain blank: {item_id}")
        items.append(
            BenchmarkItem(
                id=item_id,
                source_id=_required_string(raw, "source_id", item_id),
                source_name=_required_string(raw, "source_name", item_id),
                source_url=source_url,
                published_at=_required_string(raw, "published_at", item_id),
                title_en=title,
                summary_en=summary,
                reference_title_ja=reference_title,
                reference_summary_ja=reference_summary,
                human_title_score=_score_or_none(raw.get("human_title_score"), item_id),
                human_summary_score=_score_or_none(raw.get("human_summary_score"), item_id),
                notes=str(raw.get("notes", "")),
            )
        )
    if not 30 <= len(items) <= 50:
        raise BenchmarkConfigurationError(
            f"Benchmark corpus must contain 30-50 items, got {len(items)}"
        )
    return tuple(items)


def validate_benchmark_assets(root: Path) -> tuple[int, int]:
    """Validate the committed template and candidate metadata without loading models."""

    config = load_benchmark_config(root / "config/translation_benchmark.yml", root)
    corpus = load_corpus(config.corpus_path)
    glossary = load_glossary(config.glossary_path)
    configured_source_ids = {
        feed.id for feed in load_feed_configs(root / "config/feeds.yml")
    }
    unknown_source_ids = sorted(
        {item.source_id for item in corpus} - configured_source_ids
    )
    if unknown_source_ids:
        raise BenchmarkConfigurationError(
            f"Corpus contains unknown source IDs: {', '.join(unknown_source_ids)}"
        )
    if len(glossary) < 1:
        raise BenchmarkConfigurationError("Benchmark glossary is empty")
    if not config.candidates:
        raise BenchmarkConfigurationError("Benchmark candidates are empty")
    return len(corpus), len(config.candidates)


class TransformersAdapter:
    """Lazy Marian/M2M100 adapter; optional dependencies are never imported by CI."""

    def __init__(
        self,
        candidate: BenchmarkCandidate,
        *,
        allow_download: bool,
        max_input_tokens: int,
        max_new_tokens: int,
        num_beams: int,
        protected_terms: tuple[str, ...],
    ) -> None:
        if not candidate.model_id:
            raise TranslationError(f"Candidate has no model_id: {candidate.id}")
        try:
            import torch
            from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
        except ImportError as exc:
            raise TranslationError(
                "Transformers comparison dependencies are not installed; install them locally"
            ) from exc
        load_options = {"local_files_only": not allow_download}
        self._torch = torch
        self._tokenizer = AutoTokenizer.from_pretrained(candidate.model_id, **load_options)
        self._model = AutoModelForSeq2SeqLM.from_pretrained(candidate.model_id, **load_options)
        self._model.eval()
        self._candidate = candidate
        self._max_input_tokens = max_input_tokens
        self._max_new_tokens = max_new_tokens
        self._num_beams = num_beams
        self._protected_terms = protected_terms

    def translate(self, text: str) -> str:
        protected, replacements = protect_translation_input(
            text, extra_protected_terms=self._protected_terms
        )
        inputs = self._tokenizer(
            [protected],
            return_tensors="pt",
            truncation=True,
            max_length=self._max_input_tokens,
        )
        generation_options: dict[str, Any] = {
            "max_new_tokens": self._max_new_tokens,
            "num_beams": self._num_beams,
            "do_sample": False,
        }
        if self._candidate.backend == "m2m100":
            self._tokenizer.src_lang = "en"
            generation_options["forced_bos_token_id"] = self._tokenizer.get_lang_id("ja")
        with self._torch.inference_mode():
            output = self._model.generate(**inputs, **generation_options)
        decoded = self._tokenizer.batch_decode(output, skip_special_tokens=True)[0]
        return validate_translation(restore_translation_output(decoded, replacements))


def _make_adapter(
    candidate: BenchmarkCandidate,
    config: BenchmarkConfig,
    glossary: tuple[GlossaryTerm, ...],
    *,
    allow_download: bool,
) -> BenchmarkAdapter:
    protected_terms = protected_glossary_terms(glossary)
    if candidate.backend == "argos":
        return ArgosTranslator(
            auto_install=allow_download,
            extra_protected_terms=protected_terms,
        )
    if candidate.backend in {"marian", "m2m100"}:
        return TransformersAdapter(
            candidate,
            allow_download=allow_download,
            max_input_tokens=config.max_input_tokens,
            max_new_tokens=config.max_new_tokens,
            num_beams=config.num_beams,
            protected_terms=protected_terms,
        )
    raise TranslationError(f"Unsupported benchmark backend: {candidate.backend}")


def _rss_peak_memory_mb() -> float | None:
    try:
        import resource

        value = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    except (AttributeError, ImportError, OSError):
        return None
    # macOS reports bytes; Linux reports KiB.
    return round(value / (1024 * 1024) if value > 10_000_000 else value / 1024, 2)


def _run_row(
    candidate: BenchmarkCandidate,
    item: BenchmarkItem,
    target_type: str,
    adapter: BenchmarkAdapter | None,
    adapter_error: str | None,
    glossary: tuple[GlossaryTerm, ...],
) -> dict[str, Any]:
    source = item.title_en if target_type == "title" else item.summary_en
    protected_terms = protected_glossary_terms(glossary)
    row: dict[str, Any] = {
        "candidate_id": candidate.id,
        "target_type": target_type,
        "item_id": item.id,
        "status": "unavailable" if adapter is None else "translation_failed",
        "translated_text": "",
        "quality_passed": False,
        "quality_reasons": [adapter_error] if adapter_error else [],
        "elapsed_ms": None,
        "peak_memory_mb": None,
        **TranslationFidelity(0, 0, 0, 0, 0, 0).as_dict(),
    }
    if adapter is None:
        return row
    started = time.perf_counter()
    try:
        translated = apply_glossary(adapter.translate(source), glossary)
    except Exception as exc:  # A failed candidate must not stop other candidates.
        row["quality_reasons"] = [f"translation_failed: {exc}"]
    else:
        elapsed_ms = round((time.perf_counter() - started) * 1000, 3)
        gate = check_translation_quality(
            source,
            translated,
            target_type,
            protected_terms=protected_terms,
        )
        fidelity = translation_fidelity_metrics(
            source,
            translated,
            protected_terms=protected_terms,
        )
        row.update(
            {
                "status": "translated" if gate.passed else "quality_rejected",
                "translated_text": translated,
                "quality_passed": gate.passed,
                "quality_reasons": gate.reasons,
                "elapsed_ms": elapsed_ms,
                "peak_memory_mb": _rss_peak_memory_mb(),
                **fidelity.as_dict(),
            }
        )
    return row


def _aggregate(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    aggregates: list[dict[str, Any]] = []
    groups: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for row in rows:
        groups.setdefault((row["candidate_id"], row["target_type"]), []).append(row)
    for (candidate_id, target_type), group in sorted(groups.items()):
        measured = [row for row in group if row["elapsed_ms"] is not None]
        aggregate: dict[str, Any] = {
            "candidate_id": candidate_id,
            "target_type": target_type,
            "items": len(group),
            "available": len(measured),
            "quality_passed": sum(bool(row["quality_passed"]) for row in group),
            "quality_rejected": sum(row["status"] == "quality_rejected" for row in group),
            "average_elapsed_ms": (
                round(sum(row["elapsed_ms"] for row in measured) / len(measured), 3)
                if measured
                else None
            ),
        }
        for field in (
            "numbers_total",
            "numbers_preserved",
            "urls_total",
            "urls_preserved",
            "proper_nouns_total",
            "proper_nouns_preserved",
        ):
            aggregate[field] = sum(row[field] for row in group if row["elapsed_ms"] is not None)
        aggregates.append(aggregate)
    return aggregates


def run_benchmark(
    config: BenchmarkConfig,
    *,
    candidate_ids: tuple[str, ...] = (),
    allow_download: bool = False,
) -> dict[str, Any]:
    corpus = load_corpus(config.corpus_path)
    glossary = load_glossary(config.glossary_path)
    selected = set(candidate_ids)
    candidates = tuple(
        candidate
        for candidate in config.candidates
        if not selected or candidate.id in selected
    )
    if selected and len(candidates) != len(selected):
        missing = sorted(selected - {candidate.id for candidate in candidates})
        raise BenchmarkConfigurationError(f"Unknown benchmark candidate(s): {', '.join(missing)}")
    rows: list[dict[str, Any]] = []
    for candidate in candidates:
        adapter: BenchmarkAdapter | None = None
        adapter_error: str | None = None
        try:
            adapter = _make_adapter(candidate, config, glossary, allow_download=allow_download)
        except Exception as exc:
            adapter_error = str(exc)
        for item in corpus:
            for target_type in ("title", "summary"):
                rows.append(
                    _run_row(candidate, item, target_type, adapter, adapter_error, glossary)
                )
    return {
        "version": config.version,
        "corpus_sha256": hashlib.sha256(config.corpus_path.read_bytes()).hexdigest(),
        "glossary_sha256": hashlib.sha256(config.glossary_path.read_bytes()).hexdigest(),
        "conditions": {
            "max_input_tokens": config.max_input_tokens,
            "max_new_tokens": config.max_new_tokens,
            "num_beams": config.num_beams,
            "model_download_allowed": allow_download,
        },
        "candidates": [candidate.as_dict() for candidate in candidates],
        "runs": rows,
        "aggregates": _aggregate(rows),
    }


def write_results(result: dict[str, Any], output_directory: Path) -> tuple[Path, Path, Path]:
    output_directory.mkdir(parents=True, exist_ok=True)
    json_path = output_directory / "translation-benchmark.json"
    csv_path = output_directory / "translation-benchmark.csv"
    markdown_path = output_directory / "translation-benchmark.md"
    json_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    fieldnames = (
        "candidate_id",
        "target_type",
        "item_id",
        "status",
        "quality_passed",
        "quality_reasons",
        "elapsed_ms",
        "peak_memory_mb",
        "numbers_total",
        "numbers_preserved",
        "urls_total",
        "urls_preserved",
        "proper_nouns_total",
        "proper_nouns_preserved",
        "translated_text",
    )
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in result["runs"]:
            writer.writerow({field: row[field] for field in fieldnames})
    lines = [
        "# Translation benchmark",
        "",
        "This file is generated from the committed RSS corpus; "
        "human references and scores remain blank.",
        "",
        "| Candidate | Target | Available | Gate passed | Gate rejected | Avg ms | "
        "Numbers | URLs | Proper nouns |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in result["aggregates"]:
        lines.append(
            f"| {row['candidate_id']} | {row['target_type']} | {row['available']}/{row['items']} | "
            f"{row['quality_passed']} | {row['quality_rejected']} | "
            f"{row['average_elapsed_ms'] or '—'} | "
            f"{row['numbers_preserved']}/{row['numbers_total']} | "
            f"{row['urls_preserved']}/{row['urls_total']} | "
            f"{row['proper_nouns_preserved']}/{row['proper_nouns_total']} |"
        )
    markdown_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return json_path, csv_path, markdown_path
