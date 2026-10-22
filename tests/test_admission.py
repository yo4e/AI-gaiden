from __future__ import annotations

from pathlib import Path

import pytest
import requests

from scripts.admission import (
    FILTERED_SCAN_LIMIT,
    AdmissionConfigurationError,
    AdmissionFeedReader,
    AdmissionRule,
    apply_admission,
    expand_configs_for_admission,
    load_admission_config,
    matches_ai_terms_v1,
)
from scripts.feed_reader import FeedResult
from scripts.models import FeedConfig, NormalizedItem
from scripts.utils import load_feed_configs

ROOT = Path(__file__).resolve().parents[1]


def make_config(*, source_id: str = "sourcegraph-changelog", max_items: int = 5) -> FeedConfig:
    return FeedConfig(
        id=source_id,
        name="Example Source",
        url="https://example.com/feed.xml",
        homepage="https://example.com/",
        language="en",
        enabled=True,
        priority=50,
        max_items_per_run=max_items,
        image_policy="rss_only",
        categories=("developer-tools",),
    )


def make_item(title: str, summary: str = "") -> NormalizedItem:
    return NormalizedItem(
        source_id="sourcegraph-changelog",
        source_name="Sourcegraph Technical Changelog",
        title=title,
        url="https://sourcegraph.com/changelog/example",
        canonical_url="https://sourcegraph.com/changelog/example",
        guid=None,
        published_at=None,
        date_status="unknown",
        summary=summary,
        author=None,
        image_url=None,
        image_license=None,
        dedupe_key="",
        source_homepage="https://sourcegraph.com/changelog/releases",
    )


def test_ai_terms_v1_rejects_sourcegraph_generic_self_hosted_release() -> None:
    item = make_item("Sourcegraph self-hosted 7.7.359 is now available")

    assert matches_ai_terms_v1(item) is False


@pytest.mark.parametrize(
    ("title", "summary"),
    [
        ("Cody now supports MCP tools", ""),
        ("New agent workflows", "Built for large language model applications"),
        ("Vertex AI adds a new capability", ""),
        ("Improve vector search performance", ""),
    ],
)
def test_ai_terms_v1_accepts_clear_ai_signals(title: str, summary: str) -> None:
    assert matches_ai_terms_v1(make_item(title, summary)) is True


@pytest.mark.parametrize(
    "title",
    [
        "Model configuration improvements",
        "Search performance improvements",
        "Runtime version 2 is available",
        "Database maintenance release",
    ],
)
def test_ai_terms_v1_rejects_ambiguous_single_signals(title: str) -> None:
    assert matches_ai_terms_v1(make_item(title)) is False


@pytest.mark.parametrize(
    ("title", "summary"),
    [
        ("Azure AI adds model inference improvements", ""),
        ("Build generative AI apps on Azure", ""),
        ("New AI agent capabilities in Microsoft Foundry", ""),
        ("Copilot updates for enterprise developers", ""),
        ("Run LLM workloads efficiently in Azure", ""),
        ("Model inference improvements for production workloads", ""),
    ],
)
def test_ai_terms_v1_accepts_microsoft_cloud_ai_articles(title: str, summary: str) -> None:
    assert matches_ai_terms_v1(make_item(title, summary)) is True


@pytest.mark.parametrize(
    ("title", "summary"),
    [
        ("Improve Azure network reliability", "Guidance for routing and connectivity"),
        ("Cloud operations best practices", "Manage infrastructure across regions"),
        ("Security updates for Azure Firewall", "New controls for network protection"),
        ("Azure Storage product update", "General availability for storage features"),
    ],
)
def test_ai_terms_v1_rejects_microsoft_cloud_non_ai_articles(title: str, summary: str) -> None:
    assert matches_ai_terms_v1(make_item(title, summary)) is False


def test_repository_admission_config_covers_filtered_and_all_sources() -> None:
    rules = load_admission_config(Path("config/admission.yml"))

    assert rules["sourcegraph-changelog"] == AdmissionRule(
        mode="filtered", policy="ai_terms_v1"
    )
    for source_id in ("microsoft-ai", "microsoft-cloud"):
        assert rules[source_id] == AdmissionRule(mode="filtered", policy="ai_terms_v1")
    for source_id in (
        "langchain-releases",
        "vllm-releases",
        "ollama-releases",
        "llama-cpp-releases",
    ):
        assert rules[source_id] == AdmissionRule(mode="all")


@pytest.mark.parametrize("source_id", ["microsoft-ai", "microsoft-cloud"])
def test_microsoft_feeds_filter_shared_articles_with_repository_config(
    source_id: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    configs = {config.id: config for config in load_feed_configs(ROOT / "config/feeds.yml")}
    config = configs[source_id]
    rules = load_admission_config(ROOT / "config/admission.yml")
    reader = AdmissionFeedReader(
        tmp_path / "feed-state.json",
        {key: rule for key, rule in rules.items() if key == source_id},
    )
    # Shared synthetic RSS: AI entries follow a full publication cap of non-AI entries.
    articles = [
        (f"Azure network reliability update {index}", "Routing and connectivity guidance")
        for index in range(config.max_items_per_run)
    ]
    ai_articles = [
        ("Azure AI model update", "New capabilities for developers"),
        ("Copilot enterprise update", "New capabilities for developers"),
        ("Cloud product update", "Build generative AI applications"),
        ("Model inference improvements", "New capabilities for developers"),
        ("LLM workload update", "New capabilities for developers"),
        ("AI agent tools update", "New capabilities for developers"),
    ]
    articles.extend(ai_articles)
    entries = "".join(
        f"<item><title>{title}</title><description>{summary}</description>"
        f"<link>https://example.com/shared-article-{index}</link>"
        "<pubDate>Thu, 22 Oct 2026 00:00:00 GMT</pubDate></item>"
        for index, (title, summary) in enumerate(articles)
    )
    response = requests.Response()
    response.status_code = 200
    response.headers["Content-Type"] = "application/rss+xml"
    response.url = configs["microsoft-cloud"].url
    response._content = (
        f'<rss version="2.0"><channel><title>Shared feed</title>{entries}</channel></rss>'
    ).encode()
    monkeypatch.setattr(reader.rss_reader.session, "get", lambda *args, **kwargs: response)

    (result,) = reader.fetch_all([config])

    assert result.success is True
    assert result.config == config
    assert [item.title for item in result.items] == [
        title for title, _ in ai_articles[: config.max_items_per_run]
    ]
    assert all(item.source_id == source_id for item in result.items)


def test_filtered_sources_scan_deeper_without_changing_publication_cap() -> None:
    config = make_config(max_items=5)
    rules = {config.id: AdmissionRule(mode="filtered", policy="ai_terms_v1")}

    expanded = expand_configs_for_admission([config], rules)

    assert expanded[0].max_items_per_run == FILTERED_SCAN_LIMIT
    assert config.max_items_per_run == 5


def test_apply_admission_filters_and_restores_original_config_limit() -> None:
    config = make_config(max_items=2)
    expanded_config = make_config(max_items=FILTERED_SCAN_LIMIT)
    items = tuple(
        make_item(title)
        for title in (
            "Sourcegraph self-hosted 7.7.359 is now available",
            "Cody adds MCP support",
            "LLM inference improvements",
            "AI agent tools are available",
        )
    )
    rules = {config.id: AdmissionRule(mode="filtered", policy="ai_terms_v1")}
    results = [FeedResult(expanded_config, True, False, items)]

    admitted = apply_admission(results, rules, {config.id: config})

    assert admitted[0].config.max_items_per_run == 2
    assert [item.title for item in admitted[0].items] == [
        "Cody adds MCP support",
        "LLM inference improvements",
    ]


def test_sources_without_admission_rule_default_to_all() -> None:
    config = make_config(source_id="openai-news")
    item = make_item("A company update with no AI keyword")
    result = FeedResult(config, True, False, (item,))

    admitted = apply_admission([result], {})

    assert admitted[0].items == (item,)


def test_admission_reader_rejects_unknown_configured_source(tmp_path: Path) -> None:
    config = make_config()
    reader = AdmissionFeedReader(
        tmp_path / "feed-state.json",
        {"missing-source": AdmissionRule(mode="filtered", policy="ai_terms_v1")},
    )

    with pytest.raises(AdmissionConfigurationError, match="not configured feeds"):
        reader.fetch_all([config])


def test_invalid_filtered_policy_fails_safely(tmp_path: Path) -> None:
    config_path = tmp_path / "admission.yml"
    config_path.write_text(
        """sources:
  sourcegraph-changelog:
    mode: filtered
    policy: unknown_policy
""",
        encoding="utf-8",
    )

    with pytest.raises(AdmissionConfigurationError, match="must use policy ai_terms_v1"):
        load_admission_config(config_path)
