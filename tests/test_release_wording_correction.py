from pathlib import Path

import pytest

from scripts.correct_release_wording import correct_article, correct_releases
from scripts.utils import parse_frontmatter

ROOT = Path(__file__).resolve().parents[1]


def legacy_data() -> dict:
    from datetime import UTC, datetime

    from scripts.content_writer import article_data_from_item, build_brief
    from scripts.models import PreparedItem

    item = PreparedItem(
        source_id="ollama-releases",
        source_name="Ollama Releases",
        title_ja="更新の公開",
        title_original="Update",
        brief_ja="",
        url="https://github.com/ollama/ollama/releases/tag/v1",
        canonical_url="https://github.com/ollama/ollama/releases/tag/v1",
        published_at=datetime(2026, 9, 1, tzinfo=UTC),
        image_url=None,
        image_license=None,
        author=None,
        translation_status="complete",
        dedupe_key="fixture",
        source_type="rss",
    )
    from dataclasses import replace

    item = replace(item, brief_ja=build_brief(item, "公開された更新内容です" * 100))
    return article_data_from_item(item, generated_at=datetime(2026, 9, 1, tzinfo=UTC))


def test_correction_preserves_identity_translation_and_disclosure() -> None:
    data = legacy_data()
    revised = correct_article(data, updated_at="2026-10-27T01:15:00Z")
    changed = {key for key in data if data[key] != revised[key]}
    assert changed == {"briefJa", "description", "excerptJa", "updatedAt", "correctionHistory"}
    for key in ("briefJa", "description", "excerptJa"):
        assert "公式RSS" not in revised[key]
        assert "公式フィード" not in revised[key]
    assert revised["briefJa"].endswith("リンク先の公式発表をご確認ください。")
    assert len(revised["briefJa"]) <= 320
    assert correct_article(revised, updated_at="2026-10-28T01:15:00Z") == revised


@pytest.mark.parametrize("protection", ["humanEdited", "correctionHistory", "body", "rss"])
def test_correction_dry_run_and_protected_content(tmp_path, protection) -> None:
    from scripts.content_writer import render_article_markdown

    candidate = tmp_path / "candidate.md"
    candidate.write_text(render_article_markdown(legacy_data()))
    data = legacy_data()
    if protection == "humanEdited":
        data["humanEdited"] = True
    if protection == "correctionHistory":
        data["correctionHistory"] = [{"date": "2026-10-01", "description": "既存訂正"}]
    if protection == "rss":
        data["sourceId"] = "openai-news"
    protected = tmp_path / "protected.md"
    protected.write_text(
        render_article_markdown(data) + ("手動追記\n" if protection == "body" else "")
    )
    before = {p: p.read_bytes() for p in (candidate, protected)}
    kwargs = {"updated_at": "2026-10-27T01:15:00Z"}
    assert correct_releases(tmp_path, ROOT / "config/feeds.yml", apply=False, **kwargs)[0] == 1
    assert all(p.read_bytes() == value for p, value in before.items())
    assert correct_releases(tmp_path, ROOT / "config/feeds.yml", apply=True, **kwargs)[0] == 1
    assert protected.read_bytes() == before[protected]
    assert "公式GitHub Releases" in parse_frontmatter(candidate)["briefJa"]
    assert correct_releases(tmp_path, ROOT / "config/feeds.yml", apply=True, **kwargs)[0] == 0
