from __future__ import annotations

import logging
import re
from abc import ABC, abstractmethod

from scripts.translation_quality import PROTECTED_TERMS


class TranslationError(RuntimeError):
    """Raised when local translation is unavailable or produces unusable output."""


class Translator(ABC):
    @abstractmethod
    def translate(self, text: str) -> str:
        """Translate English text to Japanese without a network translation service."""


URL_RE = re.compile(r"https?://[^\s]+")
VERSION_RE = re.compile(r"\b(?:v?\d+(?:\.\d+){1,3}|[A-Z]{2,}[A-Z0-9.-]*)\b")
CONTROL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


def _protect(text: str) -> tuple[str, dict[str, str]]:
    replacements: dict[str, str] = {}

    def replace(value: str) -> str:
        token = f"ZXQ{len(replacements):04d}QXZ"
        replacements[token] = value
        return token

    protected = URL_RE.sub(lambda match: replace(match.group(0)), text)
    for term in sorted(PROTECTED_TERMS, key=len, reverse=True):
        protected = re.sub(re.escape(term), lambda match: replace(match.group(0)), protected)
    protected = VERSION_RE.sub(lambda match: replace(match.group(0)), protected)
    return protected, replacements


def _restore(text: str, replacements: dict[str, str]) -> str:
    restored = text
    for token, value in reversed(list(replacements.items())):
        restored = restored.replace(token, value)
        # Some translation models insert spaces inside placeholder boundaries.
        spaced = " ".join(token)
        restored = restored.replace(spaced, value)
    return restored


def validate_translation(value: str, *, maximum: int = 1000) -> str:
    result = re.sub(r"\s+", " ", value).strip()
    if (
        not result
        or len(result) > maximum
        or CONTROL_RE.search(result)
        or re.search(r"ZXQ\d{4}QXZ", result)
    ):
        raise TranslationError("Local translation returned invalid text")
    return result


class ArgosTranslator(Translator):
    """English-to-Japanese adapter backed by an installed Argos package."""

    def __init__(self, *, auto_install: bool = False) -> None:
        try:
            import argostranslate.package as package
            import argostranslate.translate as translate
        except ImportError as exc:
            raise TranslationError("Argos Translate is not installed") from exc

        # Argos logs source and translated text at INFO; repository logs only aggregate counts.
        logging.getLogger("argostranslate").setLevel(logging.WARNING)
        logging.getLogger("argostranslate.utils").setLevel(logging.WARNING)
        logging.getLogger("stanza").setLevel(logging.WARNING)

        self._package = package
        self._translate_module = translate
        if not self._has_language_pair() and auto_install:
            self._install_language_pair()
        if not self._has_language_pair():
            raise TranslationError(
                "Argos English-to-Japanese package is missing; run with ARGOS_AUTO_INSTALL=1"
            )

    def _has_language_pair(self) -> bool:
        languages = self._translate_module.get_installed_languages()
        source = next((language for language in languages if language.code == "en"), None)
        target = next((language for language in languages if language.code == "ja"), None)
        if not source or not target:
            return False
        try:
            source.get_translation(target)
        except Exception:
            return False
        return True

    def _install_language_pair(self) -> None:
        try:
            self._package.update_package_index()
            candidates = [
                item
                for item in self._package.get_available_packages()
                if item.from_code == "en" and item.to_code == "ja"
            ]
            if not candidates:
                raise TranslationError("Argos package index has no English-to-Japanese model")
            package_path = candidates[0].download()
            self._package.install_from_path(package_path)
        except TranslationError:
            raise
        except Exception as exc:
            raise TranslationError(f"Could not install Argos language package: {exc}") from exc

    def translate(self, text: str) -> str:
        if not text.strip():
            return ""
        protected, replacements = _protect(text)
        try:
            translated = self._translate_module.translate(protected, "en", "ja")
        except Exception as exc:
            raise TranslationError(f"Argos translation failed: {exc}") from exc
        return validate_translation(_restore(translated, replacements))


def limit_summary(value: str, maximum: int = 400) -> str:
    """Keep at most two feed-summary sentences and maximum English characters."""
    normalized = re.sub(r"\s+", " ", value).strip()
    normalized = re.sub(
        r"\s*The post .{0,240}? appeared first on .+?[.!]?$", "", normalized, flags=re.I
    ).strip()
    if re.match(
        r"^(?:an?\s+)?(?:illustration|illustrated|image|photo)\s+(?:of|showing)\b",
        normalized,
        flags=re.I,
    ):
        return ""
    if not normalized:
        return ""
    matches = list(re.finditer(r"[.!?](?:[\"')\]]+)?(?:\s|$)", normalized))
    if len(matches) >= 2:
        normalized = normalized[: matches[1].end()].strip()
    if len(normalized) <= maximum:
        return normalized
    return f"{normalized[: maximum - 1].rstrip()}…"
