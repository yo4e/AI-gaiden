"""Small, reviewable glossary used by offline translation comparison runs."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import yaml

URL_RE = re.compile(r"https?://[^\s]+")


@dataclass(frozen=True)
class GlossaryTerm:
    source: str
    target: str
    protect: bool = False


def load_glossary(path: Path) -> tuple[GlossaryTerm, ...]:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict) or not isinstance(raw.get("terms"), list):
        raise ValueError("Glossary must contain a terms list")
    terms: list[GlossaryTerm] = []
    seen: set[str] = set()
    for index, item in enumerate(raw["terms"]):
        if not isinstance(item, dict):
            raise ValueError(f"Glossary term {index} must be a mapping")
        source = str(item.get("source", "")).strip()
        target = str(item.get("target", "")).strip()
        if not source or not target or "\n" in source or "\n" in target:
            raise ValueError(f"Glossary term {index} must have non-empty one-line source/target")
        key = source.casefold()
        if key in seen:
            raise ValueError(f"Duplicate glossary source term: {source}")
        seen.add(key)
        terms.append(GlossaryTerm(source=source, target=target, protect=bool(item.get("protect"))))
    if not terms:
        raise ValueError("Glossary must not be empty")
    return tuple(terms)


def protected_glossary_terms(terms: tuple[GlossaryTerm, ...]) -> tuple[str, ...]:
    return tuple(term.source for term in terms if term.protect)


def apply_glossary(text: str, terms: tuple[GlossaryTerm, ...]) -> str:
    """Apply explicit target spellings without altering URLs or protected names."""

    def apply_to_non_url(segment: str) -> str:
        result = segment
        for term in sorted(terms, key=lambda item: len(item.source), reverse=True):
            if term.protect or term.source == term.target:
                continue
            result = re.sub(re.escape(term.source), term.target, result, flags=re.IGNORECASE)
        return result

    pieces: list[str] = []
    cursor = 0
    for match in URL_RE.finditer(text):
        pieces.append(apply_to_non_url(text[cursor : match.start()]))
        pieces.append(match.group(0))
        cursor = match.end()
    pieces.append(apply_to_non_url(text[cursor:]))
    return "".join(pieces)
