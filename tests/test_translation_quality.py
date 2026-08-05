from __future__ import annotations

from scripts.translation_quality import check_translation_quality
from scripts.translator import limit_summary


def test_normal_japanese_translation_passes() -> None:
    result = check_translation_quality(
        "Example Model v2.1 is available",
        "Example Model v2.1が利用可能になりました",
        "title",
    )

    assert result.passed is True
    assert result.reasons == []


def test_empty_translation_is_rejected() -> None:
    result = check_translation_quality("A useful announcement", "", "summary")

    assert result.passed is False
    assert "empty_translation" in result.reasons


def test_placeholder_remaining_is_rejected() -> None:
    result = check_translation_quality("OpenAI API update", "ZXQ0001QXZの更新", "title")

    assert result.passed is False
    assert "placeholder_remaining" in result.reasons


def test_malformed_protected_placeholder_is_rejected() -> None:
    result = check_translation_quality(
        "Amazon Bedrock Browser update",
        "Amazon Bedrock ZX0005QXZ Browserの更新",
        "summary",
    )

    assert result.passed is False
    assert "placeholder_remaining" in result.reasons


def test_missing_number_is_rejected() -> None:
    result = check_translation_quality(
        "Revenue increased by 22% with v2.1",
        "収益が増加しました",
        "summary",
    )

    assert result.passed is False
    assert "missing_number" in result.reasons


def test_version_and_percentage_are_preserved() -> None:
    result = check_translation_quality(
        "Revenue increased by 22% with v2.1",
        "v2.1で収益が22%増加しました",
        "summary",
    )

    assert result.passed is True


def test_missing_product_name_is_rejected() -> None:
    result = check_translation_quality(
        "OpenAI launches ChatGPT Work",
        "新しい仕事向けサービスを発表しました",
        "title",
    )

    assert result.passed is False
    assert "missing_proper_noun" in result.reasons


def test_general_title_case_phrases_can_be_translated() -> None:
    cases = (
        (
            "Automated Reasoning policy refinement in Amazon Bedrock",
            "Amazon Bedrockにおける自動推論ポリシーの改善",
        ),
        (
            "Understanding Alignment in Multimodal LLMs",
            "マルチモーダルLLMにおけるアラインメントの理解",
        ),
        (
            "How Formula improves automated workflows",
            "数式が自動化ワークフローをどう改善するか",
        ),
        (
            "ChatGPT Work helps legal teams",
            "ChatGPTが法務チームの業務を支援",
        ),
    )

    for source, translated in cases:
        result = check_translation_quality(source, translated, "title")
        assert result.passed is True, (source, result.reasons)


def test_explicit_additional_protected_term_is_enforced() -> None:
    result = check_translation_quality(
        "Project Aurora launches a research tool",
        "新しい研究ツールを公開しました",
        "title",
        protected_terms=("Project Aurora",),
    )

    assert result.passed is False
    assert "missing_proper_noun" in result.reasons


def test_unnatural_repetition_is_rejected() -> None:
    result = check_translation_quality(
        "A model update",
        "モデルの更新モデルの更新モデルの更新です",
        "summary",
    )

    assert result.passed is False
    assert "excessive_repetition" in result.reasons


def test_some_english_product_terms_are_not_over_rejected() -> None:
    result = check_translation_quality(
        "OpenAI API launches a new model",
        "OpenAI APIの新しいモデルを公開しました",
        "title",
    )

    assert result.passed is True


def test_url_missing_or_broken_is_rejected() -> None:
    missing = check_translation_quality(
        "Read https://example.com/news for details",
        "詳細をご確認ください",
        "summary",
    )
    broken = check_translation_quality(
        "Read https://example.com/news for details",
        "詳細はhttps://をご確認ください",
        "summary",
    )

    assert "missing_url" in missing.reasons
    assert "invalid_url" in broken.reasons


def test_symbol_only_and_known_bad_translation_are_rejected() -> None:
    symbol_only = check_translation_quality("A title", "---...", "title")
    known_bad = check_translation_quality(
        "Amazon Bedrock policy refinement",
        "Betrockのポリシー改良",
        "title",
    )

    assert "symbol_only" in symbol_only.reasons
    assert "known_mistranslation" in known_bad.reasons


def test_image_caption_is_treated_as_missing_summary() -> None:
    assert limit_summary("Illustration of a model diagram on a blue background") == ""
