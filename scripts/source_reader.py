from __future__ import annotations

from pathlib import Path

from scripts.feed_reader import FeedReader, FeedResult
from scripts.github_release_reader import GitHubReleaseReader
from scripts.models import FeedConfig


class SourceReader:
    """Dispatch configured official sources to transport-specific readers."""

    def __init__(self, cache_path: Path) -> None:
        self.use_conditional_requests = True
        self.rss_reader = FeedReader(cache_path)
        github_cache = cache_path.with_name(f"{cache_path.stem}-github-releases{cache_path.suffix}")
        self.github_release_reader = GitHubReleaseReader(github_cache)

    def fetch_all(self, configs: list[FeedConfig]) -> list[FeedResult]:
        enabled = [config for config in configs if config.enabled]
        rss_configs = [config for config in enabled if config.source_type == "rss"]
        github_configs = [
            config for config in enabled if config.source_type == "github_releases"
        ]

        self.rss_reader.use_conditional_requests = self.use_conditional_requests
        self.github_release_reader.use_conditional_requests = self.use_conditional_requests
        results = [
            *self.rss_reader.fetch_all(rss_configs),
            *self.github_release_reader.fetch_all(github_configs),
        ]
        result_by_id = {result.config.id: result for result in results}
        return [result_by_id[config.id] for config in enabled if config.id in result_by_id]
