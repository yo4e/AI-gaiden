from __future__ import annotations

from scripts.feed_reader import FeedResult
from scripts.models import FeedConfig
from scripts.source_reader import SourceReader


def make_config(source_id: str, source_type: str) -> FeedConfig:
    repository = "example-org/example-ai" if source_type == "github_releases" else None
    url = (
        "https://api.github.com/repos/example-org/example-ai/releases/latest"
        if repository
        else "https://example.com/feed.xml"
    )
    homepage = (
        "https://github.com/example-org/example-ai/releases"
        if repository
        else "https://example.com/"
    )
    return FeedConfig(
        id=source_id,
        name=source_id,
        url=url,
        homepage=homepage,
        language="en",
        enabled=True,
        priority=50,
        max_items_per_run=1,
        image_policy="rss_only",
        categories=("artificial-intelligence",),
        source_type=source_type,
        repository=repository,
    )


class FakeReader:
    def __init__(self) -> None:
        self.use_conditional_requests = True
        self.received: list[str] = []

    def fetch_all(self, configs: list[FeedConfig]) -> list[FeedResult]:
        self.received = [config.id for config in configs]
        return [FeedResult(config, True, False, ()) for config in configs]


def test_dispatches_sources_without_changing_input_order(tmp_path) -> None:
    rss = make_config("rss-source", "rss")
    github = make_config("github-source", "github_releases")
    reader = SourceReader(tmp_path / "feed-state.json")
    fake_rss = FakeReader()
    fake_github = FakeReader()
    reader.rss_reader = fake_rss
    reader.github_release_reader = fake_github
    reader.use_conditional_requests = False

    results = reader.fetch_all([github, rss])

    assert fake_rss.received == ["rss-source"]
    assert fake_github.received == ["github-source"]
    assert fake_rss.use_conditional_requests is False
    assert fake_github.use_conditional_requests is False
    assert [result.config.id for result in results] == ["github-source", "rss-source"]
