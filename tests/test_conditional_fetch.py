from __future__ import annotations

from pathlib import Path

from scripts.feed_reader import FeedReader


def test_feed_reader_can_disable_conditional_headers(tmp_path: Path) -> None:
    reader = FeedReader(tmp_path / "feed-state.json")
    assert reader.use_conditional_requests is True
    reader.use_conditional_requests = False
    assert reader.use_conditional_requests is False
