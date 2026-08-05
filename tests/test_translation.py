from __future__ import annotations

from dataclasses import replace

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


def test_malformed_protected_placeholder_is_rejected() -> None:
    with pytest.raises(TranslationError):
        validate_translation("Amazon Bedrock ZX0005QXZ Browser")


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


class TitleOnlyQualityFailureTranslator:
    def translate(self, text: str) -> str:
        if "Example Model" in text:
            return "モデルが利用可能になりました"
        return "公式RSSの研究タスク向けモデルについて説明しています"


class SummaryOnlyQualityFailureTranslator:
    def translate(self, text: str) -> str:
        if "Example Model" in text:
            return "Example Model v2.1が利用可能になりました"
        return "The team introduced a model for documented research tasks"


class MalformedPlaceholderTranslator:
    def translate(self, text: str) -> str:
        if "Example Model" in text:
            return "Example Model ZX0005QXZ"
        return "研究チームが公式発表の概要を公開しました"


def test_title_translation_failure_uses_original_title_fallback(fixture_dir, feed_config) -> None:
    from scripts.feed_reader import parse_feed_bytes

    item = parse_feed_bytes((fixture_dir / "rss.xml").read_bytes(), feed_config)[0]
    prepared = _prepare_item(item, FailingTranslator())

    assert prepared.title_ja == item.title
    assert prepared.title_translation_status == "translation_failed"
    assert prepared.title_fallback_applied is True
    assert prepared.title_fallback_reasons == ("translation_failed",)


def test_title_quality_failure_does_not_reject_summary(fixture_dir, feed_config) -> None:
    from scripts.feed_reader import parse_feed_bytes

    item = parse_feed_bytes((fixture_dir / "rss.xml").read_bytes(), feed_config)[0]
    prepared = _prepare_item(item, TitleOnlyQualityFailureTranslator())

    assert prepared.title_ja == item.title
    assert prepared.title_translation_status == "quality_rejected"
    assert prepared.summary_translation_status == "translated"
    assert prepared.summary_fallback_applied is False


def test_malformed_placeholder_uses_original_title_fallback(fixture_dir, feed_config) -> None:
    from scripts.feed_reader import parse_feed_bytes

    item = parse_feed_bytes((fixture_dir / "rss.xml").read_bytes(), feed_config)[0]
    prepared = _prepare_item(item, MalformedPlaceholderTranslator())

    assert prepared.title_ja == item.title
    assert prepared.title_translation_status == "quality_rejected"
    assert prepared.title_fallback_applied is True
    assert "placeholder_remaining" in prepared.title_fallback_reasons


def test_summary_quality_failure_keeps_translated_title(fixture_dir, feed_config) -> None:
    from scripts.feed_reader import parse_feed_bytes

    item = parse_feed_bytes((fixture_dir / "rss.xml").read_bytes(), feed_config)[0]
    prepared = _prepare_item(item, SummaryOnlyQualityFailureTranslator())

    assert prepared.title_ja == "Example Model v2.1が利用可能になりました"
    assert prepared.title_translation_status == "translated"
    assert prepared.summary_translation_status == "quality_rejected"
    assert prepared.summary_fallback_applied is True
    assert "概要の翻訳を掲載できないため" in prepared.brief_ja


def test_missing_summary_is_recorded_as_source_missing(fixture_dir, feed_config) -> None:
    from scripts.feed_reader import parse_feed_bytes

    item = parse_feed_bytes((fixture_dir / "rss.xml").read_bytes(), feed_config)[0]
    prepared = _prepare_item(
        replace(item, summary="Illustration of a model diagram on a blue background"),
        SummaryOnlyQualityFailureTranslator(),
    )

    assert prepared.summary_translation_status == "source_missing"
    assert prepared.summary_fallback_reasons == ("source_missing",)
    assert prepared.title_translation_status == "translated"
