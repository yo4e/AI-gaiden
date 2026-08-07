from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.report_quality_metrics import collect_quality_metrics, render_markdown

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests/fixtures/quality_metrics"


def metric(report: dict, path: tuple[str, ...]) -> dict:
    value = report
    for key in path:
        value = value[key]
    return value


def test_quality_metrics_cover_overall_source_date_and_reason_counts() -> None:
    report = collect_quality_metrics(FIXTURES)

    assert report["schemaVersion"] == 1
    assert report["totalArticles"] == 5
    assert report["overall"]["statuses"]["translationStatus"]["counts"] == {
        "complete": 2,
        "partial": 3,
    }
    assert metric(
        report,
        ("overall", "fallback", "titleFallbackApplied", "metrics", "true"),
    ) == {
        "count": 2,
        "denominator": 4,
        "denominatorType": "field_present",
        "rate": 0.5,
    }
    assert metric(
        report,
        ("overall", "fallbackReasons", "summaryFallbackReasons", "counts"),
    ) == {"source_missing": 1, "translation_failed": 1}
    assert metric(
        report,
        ("overall", "qualityIssues", "summaryTranslationFailed"),
    )["count"] == 1
    assert report["overall"]["humanEdited"]["missing"] == 1
    assert report["overall"]["humanEdited"]["metrics"]["true"]["denominator"] == 4
    assert report["overall"]["correctionHistory"]["count"] == 1
    assert report["overall"]["correctionHistory"]["denominator"] == 4

    assert list(report["bySource"]) == ["source-a", "source-b"]
    assert report["bySource"]["source-a"]["totalArticles"] == 3
    assert report["bySource"]["source-b"]["totalArticles"] == 2
    assert list(report["byDate"]) == [
        "2026-08-01",
        "2026-08-02",
        "2026-08-03",
        "2026-08-04",
    ]


def test_filters_are_inclusive_and_composable() -> None:
    report = collect_quality_metrics(
        FIXTURES,
        source="source-b",
        from_date="2026-08-02",
        to_date="2026-08-02",
    )

    assert report["filters"] == {
        "source": "source-b",
        "from": "2026-08-02",
        "to": "2026-08-02",
    }
    assert report["totalArticles"] == 1
    assert report["overall"]["qualityIssues"]["summaryTranslationFailed"]["count"] == 1
    assert list(report["bySource"]) == ["source-b"]
    assert list(report["byDate"]) == ["2026-08-02"]


def test_missing_fields_and_zero_denominators_are_safe(tmp_path: Path) -> None:
    empty_dir = tmp_path / "articles"
    empty_dir.mkdir()
    report = collect_quality_metrics(empty_dir)

    assert report["totalArticles"] == 0
    assert metric(
        report,
        ("overall", "fallback", "titleFallbackApplied", "metrics", "true"),
    )["rate"] is None
    assert metric(
        report,
        ("overall", "correctionHistory", "metric"),
    )["rate"] is None
    assert "—" in render_markdown(report)


def test_report_does_not_modify_article_files() -> None:
    before = {path: path.read_bytes() for path in FIXTURES.rglob("*.md")}

    collect_quality_metrics(FIXTURES)

    after = {path: path.read_bytes() for path in FIXTURES.rglob("*.md")}
    assert after == before


def test_invalid_date_range_is_rejected() -> None:
    with pytest.raises(ValueError, match="--from"):
        collect_quality_metrics(FIXTURES, from_date="2026-08-04", to_date="2026-08-01")


def test_json_shape_and_markdown_are_deterministic() -> None:
    first = collect_quality_metrics(FIXTURES)
    second = collect_quality_metrics(FIXTURES)

    assert json.dumps(first, ensure_ascii=False, sort_keys=True) == json.dumps(
        second, ensure_ascii=False, sort_keys=True
    )
    markdown = render_markdown(first)
    assert markdown.startswith("# 翻訳品質指標\n")
    assert "## 配信元別フォールバック率" in markdown
    assert "## 日付別フォールバック率" in markdown
