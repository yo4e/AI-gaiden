from __future__ import annotations

from pathlib import Path

import pytest

from scripts.models import FeedConfig


@pytest.fixture
def fixture_dir() -> Path:
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def feed_config() -> FeedConfig:
    return FeedConfig(
        id="example-ai",
        name="Example AI",
        url="https://example.com/feed.xml",
        homepage="https://example.com/",
        language="en",
        enabled=True,
        priority=100,
        max_items_per_run=10,
        image_policy="rss_only",
        categories=("artificial-intelligence",),
    )
