from __future__ import annotations

import pytest

from scripts.translator import (
    TranslationError,
    _protect,
    _restore,
    limit_summary,
    validate_translation,
)
from scripts.updater import _prepare_item


def test_summary_is_limited_to_two_sentences_and_400_characters() -> None:
    summary = "First sentence. Second sentence! Third sentence should not be present."
    assert limit_summary(summary) == "First sentence. Second sentence!"
    assert len(limit_summary("x" * 500)) == 400
    assert limit_summary("x" * 500).endswith("…")


def test_invalid_translation_is_rejected() -> None:
    with pytest.raises(TranslationError):
        validate_translation("")
    with pytest.raises(TranslationError):
        validate_translation("bad\x00text")
    with pytest.raises(TranslationError):
        validate_translation("ZXQ0001QXZが残っています")


def test_nested_protected_terms_are_restored_in_reverse_order() -> None:
    protected, replacements = _protect("GitHub Copilot v2.1 uses GPU")
    assert _restore(protected, replacements) == "GitHub Copilot v2.1 uses GPU"


def test_feed_boilerplate_is_removed_before_translation() -> None:
    summary = (
        "Useful official summary. The post A title appeared first on The GitHub Blog."
    )
    assert limit_summary(summary) == "Useful official summary."


def test_image_caption_is_not_used_as_article_summary() -> None:
    assert limit_summary("Illustration of a model diagram on a blue background") == ""


class FailingTranslator:
    def translate(self, text: str) -> str:
        raise TranslationError(f"failed: {text}")


def test_title_translation_failure_rejects_item(fixture_dir, feed_config) -> None:
    from scripts.feed_reader import parse_feed_bytes

    item = parse_feed_bytes((fixture_dir / "rss.xml").read_bytes(), feed_config)[0]
    with pytest.raises(TranslationError):
        _prepare_item(item, FailingTranslator())
