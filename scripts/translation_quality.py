"""Conservative, model-independent checks for translated feed text."""

from __future__ import annotations

import re
from collections import Counter
from collections.abc import Iterable
from dataclasses import asdict, dataclass
from typing import Literal
from urllib.parse import urlsplit

from scripts.utils import is_http_url, normalize_url

TranslationTarget = Literal["title", "summary"]

# Keep these codes stable: they are written to article frontmatter and Actions logs.
QUALITY_GATE_REASON_CODES = (
    "empty_translation",
    "too_short",
    "too_long",
    "placeholder_remaining",
    "missing_number",
    "missing_url",
    "invalid_url",
    "missing_proper_noun",
    "excessive_repetition",
    "excessive_english",
    "symbol_only",
    "not_japanese_heading",
    "known_mistranslation",
    "invalid_characters",
    "source_missing",
    "translation_failed",
)

# These are terms that the existing Argos adapter protects. A quality gate must
# still check them after translation in case a model changes or corrupts a token.
# General Title Case phrases are deliberately excluded: ordinary concepts such as
# "Automated Reasoning" must be allowed to become natural Japanese.
PROTECTED_TERMS = (
    "Hugging Face",
    "TensorFlow",
    "PyTorch",
    "GitHub Copilot",
    "GitHub",
    "Copilot",
    "NVIDIA",
    "Google DeepMind",
    "Google",
    "Gemini",
    "Claude",
    "Llama",
    "OpenAI API",
    "OpenAI",
    "ChatGPT",
    "Codex",
    "CUDA",
    "Mistral AI",
    "Microsoft",
    "Apple",
    "Cohere",
    "MLCommons",
    "AWS",
    "Amazon Bedrock",
    "Bedrock",
    "AgentCore",
    "GPT-Live",
)

KNOWN_MISTRANSLATION_PATTERNS = (
    re.compile(r"(?<![A-Za-z0-9])Betrock(?![A-Za-z0-9])", re.IGNORECASE),
    re.compile(r"この間違った取得"),
)

_CONTROL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
_PLACEHOLDER_RE = re.compile(
    r"(?:ZXQ\d{4}QXZ|__PROTECTED_\d+__|\{\{[^}]+\}\}|\[\[[^]]+\]\])"
)
_URL_RE = re.compile(r"https?://[^\s<>\u3000]*", re.IGNORECASE)
_NUMBER_RE = re.compile(
    r"(?<![A-Za-z0-9])v?\d+(?:[.,]\d+)*(?:\s*[%％])?(?![A-Za-z0-9])",
    re.IGNORECASE,
)
_ASCII_WORD_RE = re.compile(r"\b[A-Za-z][A-Za-z0-9'-]*\b")
_JAPANESE_RE = re.compile(r"[\u3040-\u30ff\u3400-\u9fff]")
_REPEATED_ASCII_RE = re.compile(
    r"\b([A-Za-z][A-Za-z0-9'-]{1,24})(?:\s+\1){1,}\b", re.IGNORECASE
)
_REPEATED_JAPANESE_RE = re.compile(r"([\u3040-\u30ff\u3400-\u9fff]{2,12})\1{2,}")


@dataclass(frozen=True)
class QualityGateResult:
    """Machine-readable result of a conservative translation quality check."""

    passed: bool
    reasons: list[str]


@dataclass(frozen=True)
class TranslationFidelity:
    """Counts of source tokens retained by a candidate translation."""

    numbers_total: int
    numbers_preserved: int
    urls_total: int
    urls_preserved: int
    proper_nouns_total: int
    proper_nouns_preserved: int

    def as_dict(self) -> dict[str, int]:
        return asdict(self)


def _normalise(value: str | None) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def _urls(value: str) -> list[str]:
    urls: list[str] = []
    for match in _URL_RE.findall(value):
        candidate = match.rstrip(".,!?;:)]}」』。")
        urls.append(candidate)
    return urls


def _is_valid_extracted_url(value: str) -> bool:
    if not is_http_url(value):
        return False
    hostname = urlsplit(value).hostname or ""
    return (
        bool(hostname)
        and all(ord(character) < 128 for character in hostname)
        and "." in hostname
    )


def _number_tokens(value: str) -> list[str]:
    tokens: list[str] = []
    for match in _NUMBER_RE.findall(value):
        token = match.lower().replace(",", "").replace(" ", "").replace("％", "%")
        tokens.append(token)
    return tokens


def _proper_terms(value: str, extra_terms: Iterable[str] = ()) -> list[str]:
    """Return only terms that callers explicitly require to survive translation."""

    candidates = list(PROTECTED_TERMS) + [term for term in extra_terms if term]
    selected: list[str] = []
    for candidate in sorted(set(candidates), key=len, reverse=True):
        if candidate.casefold() not in value.casefold():
            continue
        if any(candidate.casefold() in existing.casefold() for existing in selected):
            continue
        selected.append(candidate)
    return selected


def _add_reason(reasons: list[str], reason: str) -> None:
    if reason not in reasons:
        reasons.append(reason)


def _preserved_count(source_values: list[str], translated_values: list[str]) -> int:
    remaining = Counter(translated_values)
    preserved = 0
    for value in source_values:
        if remaining[value] > 0:
            remaining[value] -= 1
            preserved += 1
    return preserved


def translation_fidelity_metrics(
    source_text: str,
    translated_text: str,
    *,
    protected_terms: Iterable[str] = (),
) -> TranslationFidelity:
    """Return reproducible number, URL, and explicit proper-noun retention counts."""

    source_numbers = _number_tokens(source_text)
    translated_numbers = _number_tokens(translated_text)
    source_urls = [normalize_url(url) for url in _urls(source_text)]
    translated_urls = [normalize_url(url) for url in _urls(translated_text)]
    source_terms = _proper_terms(source_text, protected_terms)
    translated_folded = translated_text.casefold()
    preserved_terms = [term for term in source_terms if term.casefold() in translated_folded]
    return TranslationFidelity(
        numbers_total=len(source_numbers),
        numbers_preserved=_preserved_count(source_numbers, translated_numbers),
        urls_total=len(source_urls),
        urls_preserved=_preserved_count(source_urls, translated_urls),
        proper_nouns_total=len(source_terms),
        proper_nouns_preserved=len(preserved_terms),
    )


def check_translation_quality(
    source_text: str,
    translated_text: str,
    target_type: TranslationTarget | str,
    *,
    protected_terms: Iterable[str] = (),
) -> QualityGateResult:
    """Check a title or summary without making a subjective fluency judgement."""

    if target_type not in {"title", "summary"}:
        raise ValueError("target_type must be 'title' or 'summary'")
    source = _normalise(source_text)
    translated = _normalise(translated_text)
    reasons: list[str] = []
    if not source:
        _add_reason(reasons, "source_missing")
    if not translated:
        _add_reason(reasons, "empty_translation")
        return QualityGateResult(False, reasons)
    if _CONTROL_RE.search(translated):
        _add_reason(reasons, "invalid_characters")
    if _PLACEHOLDER_RE.search(translated):
        _add_reason(reasons, "placeholder_remaining")

    if source:
        minimum = max(3, int(len(source) * (0.18 if target_type == "title" else 0.10)))
        maximum = 180 if target_type == "title" else 1000
        if len(translated) < minimum and len(source) >= (12 if target_type == "title" else 24):
            _add_reason(reasons, "too_short")
        if len(translated) > maximum or len(translated) > max(maximum, len(source) * 4):
            _add_reason(reasons, "too_long")

        source_numbers = _number_tokens(source)
        translated_numbers = set(_number_tokens(translated))
        if any(number not in translated_numbers for number in source_numbers):
            _add_reason(reasons, "missing_number")

        source_urls = _urls(source)
        translated_urls = _urls(translated)
        if source_urls:
            translated_normalised = {normalize_url(url) for url in translated_urls}
            for url in source_urls:
                if not any(normalize_url(url) == candidate for candidate in translated_normalised):
                    _add_reason(reasons, "missing_url")
        if any(not _is_valid_extracted_url(url) for url in translated_urls):
            _add_reason(reasons, "invalid_url")

        translated_folded = translated.casefold()
        missing_terms = [
            term
            for term in _proper_terms(source, protected_terms)
            if term.casefold() not in translated_folded
        ]
        if missing_terms:
            _add_reason(reasons, "missing_proper_noun")

    ascii_words = _ASCII_WORD_RE.findall(translated)
    japanese_characters = len(_JAPANESE_RE.findall(translated))
    if len(ascii_words) >= 3 and japanese_characters < 3:
        _add_reason(reasons, "excessive_english")
    if not re.search(r"[A-Za-z\u3040-\u30ff\u3400-\u9fff]", translated):
        _add_reason(reasons, "symbol_only")
    if target_type == "title" and japanese_characters == 0 and len(ascii_words) >= 2:
        _add_reason(reasons, "not_japanese_heading")

    word_counts = Counter(word.casefold() for word in ascii_words)
    if any(count >= 3 and len(word) >= 2 for word, count in word_counts.items()):
        _add_reason(reasons, "excessive_repetition")
    if _REPEATED_ASCII_RE.search(translated) or _REPEATED_JAPANESE_RE.search(translated):
        _add_reason(reasons, "excessive_repetition")

    if any(pattern.search(translated) for pattern in KNOWN_MISTRANSLATION_PATTERNS):
        _add_reason(reasons, "known_mistranslation")

    return QualityGateResult(not reasons, reasons)


# A descriptive alias makes the gate easy to discover for callers and tests.
evaluate_translation = check_translation_quality
evaluate_quality_gate = check_translation_quality
REASON_CODES = QUALITY_GATE_REASON_CODES
