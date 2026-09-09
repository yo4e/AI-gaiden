from __future__ import annotations

from pathlib import Path

import pytest

from scripts.utils import ConfigurationError, load_feed_configs

ROOT = Path(__file__).resolve().parents[1]


def test_repository_config_contains_initial_github_release_sources() -> None:
    configs = {config.id: config for config in load_feed_configs(ROOT / "config/feeds.yml")}

    expected = {
        "langchain-releases": "langchain-ai/langchain",
        "vllm-releases": "vllm-project/vllm",
        "ollama-releases": "ollama/ollama",
        "llama-cpp-releases": "ggml-org/llama.cpp",
    }
    for source_id, repository in expected.items():
        config = configs[source_id]
        assert config.source_type == "github_releases"
        assert config.repository == repository
        assert config.url == f"https://api.github.com/repos/{repository}/releases?per_page=20"
        assert config.max_items_per_run == 5


def test_github_release_config_rejects_non_release_list_endpoint(tmp_path: Path) -> None:
    config_path = tmp_path / "feeds.yml"
    config_path.write_text(
        """feeds:
  - id: unsafe-releases
    name: Unsafe Releases
    source_type: github_releases
    repository: example/example
    url: https://api.github.com/repos/example/example/releases/latest
    homepage: https://github.com/example/example/releases
    language: en
    enabled: true
    priority: 1
    max_items_per_run: 5
    image_policy: rss_only
    categories: [artificial-intelligence]
""",
        encoding="utf-8",
    )

    with pytest.raises(ConfigurationError, match="official release-list endpoint"):
        load_feed_configs(config_path)


def test_rss_config_rejects_repository_metadata(tmp_path: Path) -> None:
    config_path = tmp_path / "feeds.yml"
    config_path.write_text(
        """feeds:
  - id: rss-source
    name: RSS Source
    repository: example/example
    url: https://example.com/feed.xml
    homepage: https://example.com/
    language: en
    enabled: true
    priority: 1
    max_items_per_run: 1
    image_policy: rss_only
    categories: [artificial-intelligence]
""",
        encoding="utf-8",
    )

    with pytest.raises(ConfigurationError, match="only valid for GitHub Releases"):
        load_feed_configs(config_path)
