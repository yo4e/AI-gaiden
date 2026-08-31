from __future__ import annotations

import logging
import re
from collections.abc import Mapping
from dataclasses import dataclass, replace
from pathlib import Path

import yaml

from scripts.feed_reader import FeedReader, FeedResult
from scripts.models import FeedConfig, NormalizedItem

LOGGER = logging.getLogger(__name__)
FILTERED_SCAN_LIMIT = 20


class AdmissionConfigurationError(ValueError):
    """Raised when source admission configuration is invalid."""


@dataclass(frozen=True, slots=True)
class AdmissionRule:
    mode: str
    policy: str | None = None


DEFAULT_RULE = AdmissionRule(mode="all")

_STRONG_PATTERNS = tuple(
    re.compile(pattern, re.IGNORECASE)
    for pattern in (
        r"\bartificial intelligence\b",
        r"\bgenerative[ -]?ai\b",
        r"\bgenai\b",
        r"\bai\b",
        r"\bmachine learning\b",
        r"\bdeep learning\b",
        r"\bml\b",
        r"\bllms?\b",
        r"\blarge language models?\b",
        r"\bfoundation models?\b",
        r"\bai agents?\b",
        r"\bagentic\b",
        r"\bmcp\b",
        r"\bmodel context protocol\b",
        r"\brag\b",
        r"\bretrieval[- ]augmented generation\b",
        r"\bcopilot\b",
        r"\bgemini\b",
        r"\bclaude\b",
        r"\bgpt(?:[- ]?\d[\w.-]*)?\b",
        r"\bllama\b",
        r"\bbedrock\b",
        r"\bvertex ai\b",
        r"\bworkers ai\b",
        r"\bai gateway\b",
        r"\bapple intelligence\b",
        r"\bcody\b",
        r"\bmosaic ai\b",
    )
)

_WEAK_PATTERNS: dict[str, re.Pattern[str]] = {
    "agent": re.compile(r"\bagents?\b", re.IGNORECASE),
    "model": re.compile(r"\bmodels?\b", re.IGNORECASE),
    "inference": re.compile(r"\binference\b", re.IGNORECASE),
    "vector": re.compile(r"\bvectors?\b", re.IGNORECASE),
    "embedding": re.compile(r"\bembeddings?\b", re.IGNORECASE),
    "training": re.compile(r"\btraining\b", re.IGNORECASE),
    "sandbox": re.compile(r"\bsandboxes?\b", re.IGNORECASE),
    "computer_use": re.compile(r"\bcomputer use\b", re.IGNORECASE),
    "search": re.compile(r"\bsearch\b", re.IGNORECASE),
    "runtime": re.compile(r"\bruntime\b", re.IGNORECASE),
}

_WEAK_COMBINATIONS = tuple(
    frozenset(pair)
    for pair in (
        ("agent", "model"),
        ("agent", "inference"),
        ("agent", "sandbox"),
        ("agent", "computer_use"),
        ("model", "inference"),
        ("model", "embedding"),
        ("model", "training"),
        ("inference", "runtime"),
        ("vector", "search"),
        ("vector", "embedding"),
        ("embedding", "search"),
    )
)


def load_admission_config(path: Path) -> dict[str, AdmissionRule]:
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise AdmissionConfigurationError(f"Could not read admission configuration: {exc}") from exc
    if not isinstance(raw, dict):
        raise AdmissionConfigurationError("Admission configuration must be a mapping")
    sources = raw.get("sources", {})
    if not isinstance(sources, dict):
        raise AdmissionConfigurationError("Admission configuration sources must be a mapping")

    rules: dict[str, AdmissionRule] = {}
    for source_id, value in sources.items():
        if not isinstance(source_id, str) or not re.fullmatch(r"[a-z0-9][a-z0-9-]*", source_id):
            raise AdmissionConfigurationError(f"Invalid admission source id: {source_id}")
        if not isinstance(value, dict):
            raise AdmissionConfigurationError(f"Admission rule must be a mapping: {source_id}")
        mode = str(value.get("mode", "")).strip().lower()
        policy_value = value.get("policy")
        policy = str(policy_value).strip() if policy_value is not None else None
        if mode not in {"all", "filtered", "none"}:
            raise AdmissionConfigurationError(f"Invalid admission mode for {source_id}: {mode}")
        if mode == "filtered" and policy != "ai_terms_v1":
            raise AdmissionConfigurationError(
                f"Filtered source {source_id} must use policy ai_terms_v1"
            )
        if mode != "filtered" and policy is not None:
            raise AdmissionConfigurationError(
                f"Admission policy is only valid for filtered sources: {source_id}"
            )
        rules[source_id] = AdmissionRule(mode=mode, policy=policy)
    return rules


def matches_ai_terms_v1(item: NormalizedItem) -> bool:
    text = f"{item.title}\n{item.summary}"
    if any(pattern.search(text) for pattern in _STRONG_PATTERNS):
        return True
    weak_hits = {name for name, pattern in _WEAK_PATTERNS.items() if pattern.search(text)}
    return any(required <= weak_hits for required in _WEAK_COMBINATIONS)


def expand_configs_for_admission(
    configs: list[FeedConfig], rules: Mapping[str, AdmissionRule]
) -> list[FeedConfig]:
    expanded: list[FeedConfig] = []
    for config in configs:
        rule = rules.get(config.id, DEFAULT_RULE)
        if rule.mode == "filtered" and config.max_items_per_run < FILTERED_SCAN_LIMIT:
            expanded.append(replace(config, max_items_per_run=FILTERED_SCAN_LIMIT))
        else:
            expanded.append(config)
    return expanded


def apply_admission(
    results: list[FeedResult],
    rules: Mapping[str, AdmissionRule],
    original_configs: Mapping[str, FeedConfig] | None = None,
) -> list[FeedResult]:
    output: list[FeedResult] = []
    originals = original_configs or {}
    for result in results:
        config = originals.get(result.config.id, result.config)
        rule = rules.get(config.id, DEFAULT_RULE)
        items = result.items
        if result.success and not result.not_modified:
            if rule.mode == "none":
                items = ()
            elif rule.mode == "filtered":
                accepted = tuple(item for item in items if matches_ai_terms_v1(item))
                items = accepted[: config.max_items_per_run]
                LOGGER.info(
                    "Admission source=%s policy=%s accepted=%d rejected=%d scanned=%d",
                    config.id,
                    rule.policy,
                    len(items),
                    len(result.items) - len(accepted),
                    len(result.items),
                )
        output.append(
            FeedResult(
                config=config,
                success=result.success,
                not_modified=result.not_modified,
                items=items,
                error=result.error,
            )
        )
    return output


class AdmissionFeedReader(FeedReader):
    """Feed reader that applies article admission after RSS normalization."""

    def __init__(self, cache_path: Path, rules: Mapping[str, AdmissionRule]) -> None:
        super().__init__(cache_path)
        self.rules = dict(rules)

    def fetch_all(self, configs: list[FeedConfig]) -> list[FeedResult]:
        config_by_id = {config.id: config for config in configs}
        unknown_sources = set(self.rules) - set(config_by_id)
        if unknown_sources:
            unknown = ", ".join(sorted(unknown_sources))
            raise AdmissionConfigurationError(f"Admission sources are not configured feeds: {unknown}")
        expanded = expand_configs_for_admission(configs, self.rules)
        results = super().fetch_all(expanded)
        return apply_admission(results, self.rules, config_by_id)
