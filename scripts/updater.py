from __future__ import annotations

import logging
import os
import shutil
import tempfile
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from scripts.content_writer import article_id_for, build_brief, build_excerpt, write_article_files
from scripts.feed_reader import FeedReader
from scripts.models import NormalizedItem, PreparedItem
from scripts.translator import ArgosTranslator, TranslationError, Translator, limit_summary
from scripts.utils import (
    load_feed_configs,
    load_json,
    recover_article_metadata,
    recover_dedupe_keys,
    write_json_atomic,
)

LOGGER = logging.getLogger(__name__)
MAX_SEEN_ITEMS = 5000


class UpdateError(RuntimeError):
    """Raised when a safe news update cannot be completed."""


def _atomic_copy(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{destination.name}.", dir=destination.parent
    )
    os.close(descriptor)
    temporary_path = Path(temporary_name)
    try:
        shutil.copy2(source, temporary_path)
        os.replace(temporary_path, destination)
    except Exception:
        temporary_path.unlink(missing_ok=True)
        raise


def _load_seen_safely(seen_path: Path) -> dict[str, Any]:
    try:
        seen = load_json(seen_path, {"items": {}})
    except ValueError as exc:
        LOGGER.warning("Could not read seen.json; recovering from article files: %s", exc)
        return {"items": {}}
    if not isinstance(seen.get("items", {}), dict):
        LOGGER.warning("seen.json has no valid items object; recovering from article files")
        return {"items": {}}
    return seen


def _known_keys(seen: dict[str, Any], content_dir: Path) -> set[str]:
    stored = seen.get("items", {})
    if not isinstance(stored, dict):
        stored = {}
    return set(stored) | recover_dedupe_keys(content_dir)


def _is_recent(item: NormalizedItem, now: datetime, days: int) -> bool:
    return bool(
        item.date_status == "known"
        and item.published_at
        and now - timedelta(days=days) <= item.published_at <= now + timedelta(hours=2)
    )


def _prepare_item(
    item: NormalizedItem, translator: Translator, fetched_at: datetime | None = None
) -> PreparedItem:
    if not item.published_at:
        raise TranslationError("Cannot publish an item with an unknown date")
    title_ja = translator.translate(item.title)
    if not title_ja or len(title_ja) > 180:
        raise TranslationError("Title translation was empty or unreasonably long")
    summary_input = limit_summary(item.summary)
    translation_status = "complete" if summary_input else "partial"
    summary_ja = ""
    if summary_input:
        try:
            summary_ja = translator.translate(summary_input)
        except TranslationError as exc:
            LOGGER.warning("Summary translation failed for %s: %s", item.dedupe_key, exc)
            translation_status = "partial"

    partial = PreparedItem(
        source_id=item.source_id,
        source_name=item.source_name,
        title_ja=title_ja,
        title_original=item.title,
        brief_ja="",
        url=item.url,
        canonical_url=item.canonical_url,
        published_at=item.published_at,
        image_url=item.image_url,
        image_license=item.image_license,
        author=item.author,
        translation_status=translation_status,
        dedupe_key=item.dedupe_key,
        source_homepage=item.source_homepage,
        fetched_at=fetched_at or item.published_at,
    )
    brief = build_brief(partial, summary_ja)
    return PreparedItem(
        source_id=partial.source_id,
        source_name=partial.source_name,
        title_ja=partial.title_ja,
        title_original=partial.title_original,
        brief_ja=brief,
        url=partial.url,
        canonical_url=partial.canonical_url,
        published_at=partial.published_at,
        image_url=partial.image_url,
        image_license=partial.image_license,
        author=partial.author,
        translation_status=partial.translation_status,
        dedupe_key=partial.dedupe_key,
        source_homepage=partial.source_homepage,
        fetched_at=partial.fetched_at,
        excerpt_ja=build_excerpt(brief),
    )


def _updated_seen(
    seen: dict[str, Any],
    prepared: list[PreparedItem],
    generated_at: datetime,
    recovered: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    items = dict(seen.get("items", {}))
    for key, value in recovered.items():
        items.setdefault(key, value)
    first_seen_at = generated_at.astimezone(UTC).isoformat().replace("+00:00", "Z")
    for item in prepared:
        items[item.dedupe_key] = {
            "url": item.canonical_url,
            "source": item.source_id,
            "published_at": item.published_at.astimezone(UTC)
            .isoformat()
            .replace("+00:00", "Z"),
            "first_seen_at": first_seen_at,
            "article_id": article_id_for(item.source_id, item.dedupe_key),
        }
    if len(items) > MAX_SEEN_ITEMS:
        ordered = sorted(
            items.items(), key=lambda pair: str(pair[1].get("first_seen_at", "")), reverse=True
        )
        items = dict(ordered[:MAX_SEEN_ITEMS])
    return {"items": items}


def run_update(
    *,
    config_path: Path,
    seen_path: Path,
    content_dir: Path,
    cache_path: Path,
    bootstrap_days: int,
    now: datetime | None = None,
    reader: FeedReader | None = None,
    translator: Translator | None = None,
) -> int:
    if not 1 <= bootstrap_days <= 7:
        raise UpdateError("bootstrap_days must be between 1 and 7")
    generated_at = (now or datetime.now(UTC)).astimezone(UTC)
    configs = load_feed_configs(config_path)
    seen = _load_seen_safely(seen_path)
    recovered = recover_article_metadata(content_dir)
    known = _known_keys(seen, content_dir)
    initial_run = not known
    feed_reader = reader or FeedReader(cache_path)
    if isinstance(feed_reader, FeedReader):
        # A first/bootstrap run must be able to widen its lookback even after a cached 304.
        feed_reader.use_conditional_requests = not initial_run and bootstrap_days == 3
    results = feed_reader.fetch_all(configs)
    successes = [result for result in results if result.success]
    failures = [result for result in results if not result.success]
    for result in successes:
        LOGGER.info(
            "Feed succeeded: %s items=%d not_modified=%s",
            result.config.id,
            len(result.items),
            result.not_modified,
        )
        if not result.not_modified and not result.items:
            LOGGER.warning("Feed returned no usable entries: %s", result.config.id)
    for result in failures:
        LOGGER.warning("Feed failed: %s (%s)", result.config.id, result.error)
    if not successes:
        raise UpdateError("All enabled feeds failed; existing content was left unchanged")

    fetched_items = [item for result in successes for item in result.items]
    eligible = [
        item
        for item in fetched_items
        if _is_recent(item, generated_at, bootstrap_days)
        and item.dedupe_key
        and item.dedupe_key not in known
    ]
    priorities = {config.id: config.priority for config in configs}
    eligible.sort(
        key=lambda item: (item.published_at or generated_at, priorities.get(item.source_id, 0)),
        reverse=True,
    )
    unique: list[NormalizedItem] = []
    run_keys: set[str] = set()
    limit = 10 if initial_run else 40
    for item in eligible:
        if item.dedupe_key in run_keys:
            continue
        run_keys.add(item.dedupe_key)
        unique.append(item)
        if len(unique) >= limit:
            break

    duplicate_count = len(fetched_items) - len(eligible) + (len(eligible) - len(unique))
    LOGGER.info(
        "Feeds: configured=%d success=%d failed=%d fetched_items=%d "
        "new=%d duplicates_or_filtered=%d",
        len([config for config in configs if config.enabled]),
        len(successes),
        len(failures),
        len(fetched_items),
        len(unique),
        duplicate_count,
    )
    if not unique:
        LOGGER.info("No new publishable items; no content commit is needed")
        return 0

    local_translator = translator or ArgosTranslator(
        auto_install=os.environ.get("ARGOS_AUTO_INSTALL") == "1"
    )
    prepared: list[PreparedItem] = []
    title_failures = 0
    for item in unique:
        try:
            prepared.append(_prepare_item(item, local_translator, generated_at))
        except TranslationError as exc:
            title_failures += 1
            LOGGER.warning("Title translation failed; item skipped: %s (%s)", item.dedupe_key, exc)
    if not prepared:
        raise UpdateError("Every new item failed title translation; existing content was unchanged")

    content_dir.mkdir(parents=True, exist_ok=True)
    seen_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="ai-gaiden-update-") as temporary_root:
        temporary = Path(temporary_root)
        staged_content = temporary / "articles"
        generated_paths = write_article_files(
            prepared,
            existing_dir=content_dir,
            output_dir=staged_content,
            generated_at=generated_at,
        )
        staged_seen = temporary / "seen.json"
        write_json_atomic(staged_seen, _updated_seen(seen, prepared, generated_at, recovered))

        for staged_path in generated_paths:
            destination = content_dir / staged_path
            _atomic_copy(staged_content / staged_path, destination)
        _atomic_copy(staged_seen, seen_path)

    LOGGER.info(
        "Translation: success=%d title_failed=%d generated_pages=%s commit_needed=yes",
        len(prepared),
        title_failures,
        ",".join(path.as_posix() for path in generated_paths),
    )
    return len(prepared)
