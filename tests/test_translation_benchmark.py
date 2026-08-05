from __future__ import annotations

from pathlib import Path

import scripts.translation_benchmark as benchmark
from scripts.translation_benchmark import (
    BenchmarkCandidate,
    BenchmarkConfig,
    run_benchmark,
    validate_benchmark_assets,
    write_results,
)
from scripts.translation_glossary import apply_glossary, load_glossary
from scripts.translation_quality import translation_fidelity_metrics

ROOT = Path(__file__).resolve().parents[1]


def test_committed_benchmark_assets_are_a_blank_40_item_template() -> None:
    corpus_count, candidate_count = validate_benchmark_assets(ROOT)

    assert corpus_count == 40
    assert candidate_count == 4


def test_glossary_preserves_products_and_normalises_explicit_terms() -> None:
    glossary = load_glossary(ROOT / "config/translation_glossary.yml")

    translated = apply_glossary(
        "OpenAI API uses agentic AI for inference at https://example.com/inference",
        glossary,
    )

    assert translated == (
        "OpenAI API uses エージェント型AI for 推論 at https://example.com/inference"
    )


def test_fidelity_counts_numbers_urls_and_product_names_separately() -> None:
    source = "OpenAI API v2.1 reports 22% at https://example.com/news"
    translated = "OpenAI API v2.1で22%を確認 https://example.com/news"

    metrics = translation_fidelity_metrics(source, translated)

    assert metrics.numbers_total == 2
    assert metrics.numbers_preserved == 2
    assert metrics.urls_total == 1
    assert metrics.urls_preserved == 1
    assert metrics.proper_nouns_total == 1
    assert metrics.proper_nouns_preserved == 1


class FakeAdapter:
    def translate(self, text: str) -> str:
        return f"日本語 {text}"


def test_runner_separates_title_summary_and_writes_three_formats(tmp_path, monkeypatch) -> None:
    config = benchmark.load_benchmark_config(ROOT / "config/translation_benchmark.yml", ROOT)
    candidate = BenchmarkCandidate(
        id="fake",
        label="Fake",
        backend="test",
        model_id=None,
        package=None,
        official_url="https://example.com",
        model_card_url="https://example.com/model",
        license="test",
        commercial_status="test",
        model_size="test",
        cpu_time="not_measured",
        memory="not_measured",
        download_time="not_measured",
        cache_size="not_measured",
        actions_feasibility="test",
        production_candidate=False,
        exclusion_reason="test",
    )
    fake_config = BenchmarkConfig(
        version=config.version,
        corpus_path=config.corpus_path,
        glossary_path=config.glossary_path,
        results_directory=tmp_path,
        max_input_tokens=config.max_input_tokens,
        max_new_tokens=config.max_new_tokens,
        num_beams=config.num_beams,
        candidates=(candidate,),
    )
    monkeypatch.setattr(benchmark, "_make_adapter", lambda *args, **kwargs: FakeAdapter())

    result = run_benchmark(fake_config)
    paths = write_results(result, tmp_path)

    assert len(result["runs"]) == 80
    assert {row["target_type"] for row in result["runs"]} == {"title", "summary"}
    assert {row["status"] for row in result["runs"]} <= {
        "translated",
        "quality_rejected",
    }
    assert any(row["status"] == "quality_rejected" for row in result["runs"])
    assert all(path.exists() for path in paths)
    assert "candidate_id,target_type,item_id" in paths[1].read_text(encoding="utf-8")
