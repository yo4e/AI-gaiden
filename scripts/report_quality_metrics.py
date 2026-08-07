"""Aggregate translation-quality metrics from article frontmatter only.

The report deliberately does not inspect article Markdown bodies.  Article
frontmatter is the immutable metadata source for the pipeline, and keeping
this report offline makes it reproducible in local development and CI.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.utils import parse_frontmatter  # noqa: E402

STATUS_FIELDS = (
    "translationStatus",
    "titleTranslationStatus",
    "summaryTranslationStatus",
    "titleQualityGate",
    "summaryQualityGate",
)
FALLBACK_FIELDS = ("titleFallbackApplied", "summaryFallbackApplied")
REASON_FIELDS = (
    "titleFallbackReasons",
    "summaryFallbackReasons",
    "translationFallbackReasons",
)

_DATE_ONLY_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_OFFSET_DATETIME_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}"
    r"(?::\d{2}(?:\.\d{1,9})?)?(?:Z|[+-]\d{2}:\d{2})$"
)


@dataclass(frozen=True, slots=True)
class ArticleRecord:
    """The path and frontmatter for one article."""

    path: Path
    data: dict[str, Any]


def load_articles(content_dir: Path) -> list[ArticleRecord]:
    """Load article frontmatter in a stable path order.

    ``parse_frontmatter`` extracts only the YAML block.  The Markdown body is
    never passed to any metric calculation.
    """

    if not content_dir.exists():
        raise FileNotFoundError(f"Article directory does not exist: {content_dir}")
    if not content_dir.is_dir():
        raise NotADirectoryError(f"Article path is not a directory: {content_dir}")

    records: list[ArticleRecord] = []
    for path in sorted(content_dir.rglob("*.md")):
        records.append(ArticleRecord(path=path, data=parse_frontmatter(path)))
    return records


def _is_recorded(value: Any) -> bool:
    if value is None:
        return False
    return not isinstance(value, str) or bool(value.strip())


def _date_string(value: Any) -> str | None:
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if not isinstance(value, str):
        return None
    candidate = value.strip()
    if not _DATE_ONLY_RE.fullmatch(candidate):
        return None
    try:
        date.fromisoformat(candidate)
    except ValueError:
        return None
    return candidate


def _parse_date(value: str | date | datetime | None, option_name: str) -> date | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{option_name} must be YYYY-MM-DD: {value}") from exc


def select_articles(
    records: Iterable[ArticleRecord],
    *,
    source: str | None = None,
    from_date: str | date | None = None,
    to_date: str | date | None = None,
) -> list[ArticleRecord]:
    """Apply inclusive source and JST-date filters without changing records."""

    start = _parse_date(from_date, "--from")
    end = _parse_date(to_date, "--to")
    if start and end and start > end:
        raise ValueError("--from must be earlier than or equal to --to")

    selected: list[ArticleRecord] = []
    for record in records:
        if source is not None and record.data.get("sourceId") != source:
            continue
        article_date = _date_string(record.data.get("dateJst"))
        if start and (article_date is None or date.fromisoformat(article_date) < start):
            continue
        if end and (article_date is None or date.fromisoformat(article_date) > end):
            continue
        selected.append(record)
    return selected


def _metric(count: int, denominator: int, denominator_type: str) -> dict[str, Any]:
    rate = round(count / denominator, 6) if denominator else None
    return {
        "count": count,
        "denominator": denominator,
        "denominatorType": denominator_type,
        "rate": rate,
    }


def _display_value(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    return str(value)


def _categorical_summary(records: list[ArticleRecord], field: str) -> dict[str, Any]:
    counts = Counter(
        _display_value(record.data[field])
        for record in records
        if _is_recorded(record.data.get(field))
    )
    denominator = sum(counts.values())
    ordered_counts = {key: counts[key] for key in sorted(counts)}
    return {
        "field": field,
        "counts": ordered_counts,
        "denominator": denominator,
        "denominatorType": "field_present",
        "missing": len(records) - denominator,
        "metrics": {
            key: _metric(count, denominator, "field_present")
            for key, count in ordered_counts.items()
        },
    }


def _boolean_summary(records: list[ArticleRecord], field: str) -> dict[str, Any]:
    values = [record.data.get(field) for record in records]
    counts = Counter(value for value in values if isinstance(value, bool))
    denominator = sum(counts.values())
    ordered_counts = {key: counts.get(key, 0) for key in (False, True)}
    return {
        "field": field,
        "counts": {"false": ordered_counts[False], "true": ordered_counts[True]},
        "denominator": denominator,
        "denominatorType": "field_present",
        "missing": len(records) - denominator,
        "metrics": {
            "false": _metric(ordered_counts[False], denominator, "field_present"),
            "true": _metric(ordered_counts[True], denominator, "field_present"),
        },
    }


def _reason_summary(records: list[ArticleRecord], field: str) -> dict[str, Any]:
    counts: Counter[str] = Counter()
    for record in records:
        values = record.data.get(field)
        if not isinstance(values, list):
            continue
        reasons = {value.strip() for value in values if isinstance(value, str) and value.strip()}
        counts.update(reasons)
    ordered_counts = {key: counts[key] for key in sorted(counts)}
    return {
        "field": field,
        "counts": ordered_counts,
        "denominator": len(records),
        "denominatorType": "all_articles",
        "metrics": {
            key: _metric(count, len(records), "all_articles")
            for key, count in ordered_counts.items()
        },
    }


def _valid_date_only(value: str) -> bool:
    if not _DATE_ONLY_RE.fullmatch(value):
        return False
    try:
        date.fromisoformat(value)
    except ValueError:
        return False
    return True


def _valid_public_correction(value: Any) -> bool:
    """Match the public correction shape used by ArticleBulletin.astro."""

    if not isinstance(value, dict):
        return False
    correction_date = next(
        (
            value.get(key).strip()
            for key in ("date", "correctedAt", "updatedAt")
            if isinstance(value.get(key), str) and value.get(key).strip()
        ),
        None,
    )
    description = next(
        (
            value.get(key).strip()
            for key in ("description", "summary")
            if isinstance(value.get(key), str) and value.get(key).strip()
        ),
        None,
    )
    if not correction_date or not description:
        return False
    if _valid_date_only(correction_date):
        return True
    if not _OFFSET_DATETIME_RE.fullmatch(correction_date):
        return False
    try:
        datetime.fromisoformat(correction_date.replace("Z", "+00:00"))
    except ValueError:
        return False
    return _valid_date_only(correction_date[:10])


def _correction_summary(records: list[ArticleRecord]) -> dict[str, Any]:
    recorded = [
        record.data.get("correctionHistory")
        for record in records
        if isinstance(record.data.get("correctionHistory"), list)
    ]
    count = sum(any(_valid_public_correction(item) for item in history) for history in recorded)
    metric = _metric(count, len(recorded), "field_present")
    return {
        "field": "correctionHistory",
        "count": count,
        "denominator": len(recorded),
        "denominatorType": "field_present",
        "missing": len(records) - len(recorded),
        "metric": metric,
    }


def _quality_issue_summary(records: list[ArticleRecord]) -> dict[str, dict[str, Any]]:
    predicates: dict[str, Callable[[dict[str, Any]], bool]] = {
        "titleQualityGateRejected": lambda data: data.get("titleQualityGate") == "rejected",
        "summaryQualityGateRejected": lambda data: data.get("summaryQualityGate") == "rejected",
        "titleTranslationFailed": lambda data: data.get("titleTranslationStatus")
        == "translation_failed",
        "summaryTranslationFailed": lambda data: data.get("summaryTranslationStatus")
        == "translation_failed",
        "titleSourceMissing": lambda data: data.get("titleTranslationStatus") == "source_missing",
        "summarySourceMissing": lambda data: data.get("summaryTranslationStatus")
        == "source_missing",
        "translationStatusPartial": lambda data: data.get("translationStatus") == "partial",
    }
    return {
        name: _metric(
            sum(predicate(record.data) for record in records),
            len(records),
            "all_articles",
        )
        for name, predicate in predicates.items()
    }


def _summarize(records: list[ArticleRecord]) -> dict[str, Any]:
    return {
        "totalArticles": len(records),
        "statuses": {field: _categorical_summary(records, field) for field in STATUS_FIELDS},
        "fallback": {field: _boolean_summary(records, field) for field in FALLBACK_FIELDS},
        "fallbackReasons": {
            field: _reason_summary(records, field) for field in REASON_FIELDS
        },
        "humanEdited": _boolean_summary(records, "humanEdited"),
        "correctionHistory": _correction_summary(records),
        "qualityIssues": _quality_issue_summary(records),
    }


def _group_by(
    records: list[ArticleRecord],
    field: str,
    normalizer: Callable[[Any], str | None],
) -> dict[str, list[ArticleRecord]]:
    grouped: dict[str, list[ArticleRecord]] = {}
    for record in records:
        key = normalizer(record.data.get(field))
        if key is not None:
            grouped.setdefault(key, []).append(record)
    return {key: grouped[key] for key in sorted(grouped)}


def collect_quality_metrics(
    content_dir: Path,
    *,
    source: str | None = None,
    from_date: str | date | None = None,
    to_date: str | date | None = None,
) -> dict[str, Any]:
    """Return deterministic quality metrics for the selected article files."""

    records = select_articles(
        load_articles(content_dir),
        source=source,
        from_date=from_date,
        to_date=to_date,
    )
    normalized_from = _parse_date(from_date, "--from")
    normalized_to = _parse_date(to_date, "--to")
    report = {
        "schemaVersion": 1,
        "filters": {
            "source": source,
            "from": normalized_from.isoformat() if normalized_from else None,
            "to": normalized_to.isoformat() if normalized_to else None,
        },
        "totalArticles": len(records),
        "overall": _summarize(records),
        "bySource": {
            key: _summarize(group)
            for key, group in _group_by(
                records,
                "sourceId",
                lambda value: value.strip()
                if isinstance(value, str) and value.strip()
                else None,
            ).items()
        },
        "byDate": {
            key: _summarize(group)
            for key, group in _group_by(records, "dateJst", _date_string).items()
        },
    }
    return report


def _metric_text(metric: dict[str, Any]) -> str:
    rate = metric["rate"]
    rate_text = "—" if rate is None else f"{rate:.1%}"
    return (
        f"{metric['count']}/{metric['denominator']} "
        f"({rate_text}; 分母={metric['denominatorType']})"
    )


def _append_status_table(lines: list[str], summary: dict[str, Any]) -> None:
    lines.extend(
        [
            "| フィールド | 値 | 件数/分母 | 割合 |",
            "| --- | --- | ---: | ---: |",
        ]
    )
    for field in STATUS_FIELDS:
        field_summary = summary["statuses"][field]
        for value in sorted(field_summary["counts"]):
            metric = field_summary["metrics"][value]
            rate_text = "—" if metric["rate"] is None else f"{metric['rate']:.1%}"
            lines.append(
                f"| `{field}` | `{value}` | {metric['count']}/{metric['denominator']} "
                f"(分母={metric['denominatorType']}) | {rate_text} |"
            )
        if field_summary["missing"]:
            lines.append(
                f"| `{field}` | 欠損 | {field_summary['missing']}/{summary['totalArticles']} "
                "(分母=all_articles) | — |"
            )


def render_markdown(report: dict[str, Any]) -> str:
    """Render a stable human-readable report from ``collect_quality_metrics``."""

    overall = report["overall"]
    filters = report["filters"]
    filter_text = ", ".join(
        [
            f"source={filters['source'] or 'all'}",
            f"from={filters['from'] or 'none'}",
            f"to={filters['to'] or 'none'}",
        ]
    )
    lines = [
        "# 翻訳品質指標",
        "",
        f"- 対象記事数: **{report['totalArticles']}**",
        f"- フィルター: `{filter_text}`",
        "- 品質判定は記事本文を使わず、YAML frontmatterだけを対象にしています。",
        "- `rate`は各行に記載した分母に対する割合です。分母が0の場合は`—`と表示します。",
        "",
        "## 全体",
        "",
        "### 翻訳状態・品質ゲート",
        "",
    ]
    _append_status_table(lines, overall)
    lines.extend(["", "### フォールバック・人間修正・訂正履歴", ""])
    lines.extend(
        [
            "| 指標 | 件数/分母 | 割合 |",
            "| --- | ---: | ---: |",
        ]
    )
    for field in (*FALLBACK_FIELDS, "humanEdited"):
        field_summary = (
            overall["fallback"][field] if field in FALLBACK_FIELDS else overall["humanEdited"]
        )
        metric = field_summary["metrics"]["true"]
        rate_text = "—" if metric["rate"] is None else f"{metric['rate']:.1%}"
        lines.append(f"| `{field}=true` | {_metric_text(metric)} | {rate_text} |")
    correction_metric = overall["correctionHistory"]["metric"]
    correction_rate = (
        "—" if correction_metric["rate"] is None else f"{correction_metric['rate']:.1%}"
    )
    lines.append(
        f"| 公開可能な`correctionHistory`を持つ記事 | "
        f"{_metric_text(correction_metric)} | {correction_rate} |"
    )
    lines.extend(
        [
            "",
            "### 品質上の問題",
            "",
            "| 指標 | 件数/分母 | 割合 |",
            "| --- | ---: | ---: |",
        ]
    )
    for name, metric in overall["qualityIssues"].items():
        rate_text = "—" if metric["rate"] is None else f"{metric['rate']:.1%}"
        lines.append(f"| `{name}` | {_metric_text(metric)} | {rate_text} |")
    lines.extend(
        [
            "",
            "### フォールバック理由",
            "",
            "| フィールド | 理由 | 件数/分母 | 割合 |",
            "| --- | --- | ---: | ---: |",
        ]
    )
    for field in REASON_FIELDS:
        for reason, metric in overall["fallbackReasons"][field]["metrics"].items():
            rate_text = "—" if metric["rate"] is None else f"{metric['rate']:.1%}"
            lines.append(f"| `{field}` | `{reason}` | {_metric_text(metric)} | {rate_text} |")

    lines.extend(["", "## 配信元別フォールバック率", ""])
    lines.extend(
        [
            "| sourceId | 記事数 | タイトルフォールバック | 概要フォールバック |",
            "| --- | ---: | ---: | ---: |",
        ]
    )
    if report["bySource"]:
        for source_id, group in report["bySource"].items():
            title_metric = group["fallback"]["titleFallbackApplied"]["metrics"]["true"]
            summary_metric = group["fallback"]["summaryFallbackApplied"]["metrics"]["true"]
            lines.append(
                f"| `{source_id}` | {group['totalArticles']} | "
                f"{_metric_text(title_metric)} | {_metric_text(summary_metric)} |"
            )
    else:
        lines.append("| — | 0 | — | — |")

    lines.extend(["", "## 日付別フォールバック率", ""])
    lines.extend(
        [
            "| dateJst | 記事数 | タイトルフォールバック | 概要フォールバック |",
            "| --- | ---: | ---: | ---: |",
        ]
    )
    if report["byDate"]:
        for date_value, group in report["byDate"].items():
            title_metric = group["fallback"]["titleFallbackApplied"]["metrics"]["true"]
            summary_metric = group["fallback"]["summaryFallbackApplied"]["metrics"]["true"]
            lines.append(
                f"| `{date_value}` | {group['totalArticles']} | "
                f"{_metric_text(title_metric)} | {_metric_text(summary_metric)} |"
            )
    else:
        lines.append("| — | 0 | — | — |")
    return "\n".join(lines) + "\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Aggregate translation-quality metrics from article frontmatter "
            "without network access."
        )
    )
    parser.add_argument(
        "--articles-dir",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "src/content/articles",
        help="Article Markdown directory (default: src/content/articles)",
    )
    parser.add_argument("--format", choices=("markdown", "json"), default="markdown")
    parser.add_argument("--source", help="Filter by exact sourceId")
    parser.add_argument("--from", dest="from_date", help="Inclusive JST date filter (YYYY-MM-DD)")
    parser.add_argument("--to", dest="to_date", help="Inclusive JST date filter (YYYY-MM-DD)")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        report = collect_quality_metrics(
            args.articles_dir,
            source=args.source,
            from_date=args.from_date,
            to_date=args.to_date,
        )
    except (FileNotFoundError, NotADirectoryError, ValueError) as exc:
        parser.error(str(exc))
    if args.format == "json":
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(render_markdown(report), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
