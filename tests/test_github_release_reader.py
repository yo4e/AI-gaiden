from __future__ import annotations

import json
from datetime import UTC

import requests

from scripts.github_release_reader import GitHubReleaseReader, normalize_release
from scripts.models import FeedConfig


def make_config() -> FeedConfig:
    return FeedConfig(
        id="example-releases",
        name="Example Releases",
        url="https://api.github.com/repos/example-org/example-ai/releases/latest",
        homepage="https://github.com/example-org/example-ai/releases",
        language="en",
        enabled=True,
        priority=50,
        max_items_per_run=1,
        image_policy="rss_only",
        categories=("artificial-intelligence",),
        source_type="github_releases",
        repository="example-org/example-ai",
    )


def release_payload(**overrides):
    payload = {
        "id": 12345,
        "tag_name": "v1.2.3",
        "name": "Example AI v1.2.3",
        "html_url": "https://github.com/example-org/example-ai/releases/tag/v1.2.3",
        "draft": False,
        "prerelease": False,
        "published_at": "2026-09-08T12:34:56Z",
        "body": "## Highlights\n\n- Adds [tool calling](https://example.com/docs).",
        "author": {"login": "release-bot"},
    }
    payload.update(overrides)
    return payload


def response_for(payload, *, status: int = 200, url: str | None = None) -> requests.Response:
    response = requests.Response()
    response.status_code = status
    response.url = url or make_config().url
    response._content = json.dumps(payload).encode("utf-8")
    response.headers["Content-Type"] = "application/json"
    return response


def test_normalizes_latest_stable_release() -> None:
    item = normalize_release(release_payload(), make_config())

    assert item is not None
    assert item.title == "Example AI v1.2.3"
    assert item.canonical_url == "https://github.com/example-org/example-ai/releases/tag/v1.2.3"
    assert item.guid == "github-release:12345"
    assert item.published_at is not None
    assert item.published_at.tzinfo == UTC
    assert item.summary == "Highlights Adds tool calling."
    assert item.author == "release-bot"
    assert item.image_url is None
    assert item.dedupe_key.startswith("url:")


def test_rejects_draft_prerelease_and_cross_repository_urls() -> None:
    config = make_config()

    assert normalize_release(release_payload(draft=True), config) is None
    assert normalize_release(release_payload(prerelease=True), config) is None
    assert (
        normalize_release(
            release_payload(html_url="https://github.com/other/repo/releases/tag/v1"), config
        )
        is None
    )


def test_reader_sends_token_and_reuses_etag(tmp_path, monkeypatch) -> None:
    config = make_config()
    reader = GitHubReleaseReader(tmp_path / "github-releases.json")
    reader.cache = {"sources": {config.id: {"etag": '"release-etag"'}}}
    captured_headers = {}
    response = response_for(release_payload())
    response.headers["ETag"] = '"next-etag"'

    def fake_get(*args, **kwargs):
        captured_headers.update(kwargs["headers"])
        return response

    monkeypatch.setenv("GITHUB_TOKEN", "test-token")
    monkeypatch.setattr(reader.session, "get", fake_get)

    result, changed = reader._fetch(config)

    assert result.success is True
    assert len(result.items) == 1
    assert changed is True
    assert captured_headers["Authorization"] == "Bearer test-token"
    assert captured_headers["If-None-Match"] == '"release-etag"'
    assert captured_headers["X-GitHub-Api-Version"] == "2022-11-28"


def test_reader_handles_not_modified_without_items(tmp_path, monkeypatch) -> None:
    config = make_config()
    reader = GitHubReleaseReader(tmp_path / "github-releases.json")
    response = requests.Response()
    response.status_code = 304
    response.url = config.url
    monkeypatch.setattr(reader.session, "get", lambda *args, **kwargs: response)

    result, changed = reader._fetch(config)

    assert result.success is True
    assert result.not_modified is True
    assert result.items == ()
    assert changed is False


def test_reader_fails_safely_on_rate_limit(tmp_path, monkeypatch) -> None:
    config = make_config()
    reader = GitHubReleaseReader(tmp_path / "github-releases.json")
    response = requests.Response()
    response.status_code = 403
    response.url = config.url
    response.headers["X-RateLimit-Remaining"] = "0"
    response.headers["X-RateLimit-Reset"] = "1234567890"
    monkeypatch.setattr(reader.session, "get", lambda *args, **kwargs: response)

    result, changed = reader._fetch(config)

    assert result.success is False
    assert result.items == ()
    assert "rate limit exhausted" in (result.error or "")
    assert changed is False
