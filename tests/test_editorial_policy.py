from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_editorial_policy_has_a_stable_public_page() -> None:
    policy = (ROOT / "src/pages/editorial-policy.astro").read_text(encoding="utf-8")

    assert 'canonicalPath="/editorial-policy/"' in policy
    for phrase in (
        "RSS/Atom由来",
        "元記事ページのHTMLをスクレイピングせず",
        "自動収集、自動翻訳、定型編集",
        "原文にない評価、重要度、影響、推測、将来予測",
        "原題表示や公式リンク案内へフォールバック",
        "原文タイトル、配信元、公式発表へのリンク",
        "記事URL、公式発表URL、誤りの箇所",
        "公式発表の更新や撤回",
        "人間確認済みの解説・コラムは現在提供していません",
        "サイトRSSの利用条件",
    ):
        assert phrase in policy


def test_editorial_policy_is_reachable_from_about_and_footer() -> None:
    about = (ROOT / "src/pages/about.astro").read_text(encoding="utf-8")
    layout = (ROOT / "src/layouts/BaseLayout.astro").read_text(encoding="utf-8")

    assert 'id="editorial-policy"' in about
    assert 'href="/editorial-policy/"' in about
    assert 'href="/editorial-policy/"' in layout
    assert 'href="/about/#editorial-policy"' not in layout


def test_implementation_spec_names_the_policy_page_as_the_source_of_truth() -> None:
    spec = (ROOT / "docs/IMPLEMENTATION_SPEC.md").read_text(encoding="utf-8")

    assert "### 13.9 `/editorial-policy/`" in spec
    assert "独立した安定URLを正本" in spec
    assert "RSS利用条件と方針を`/editorial-policy/`に掲載" in spec
    assert "Aboutページの`#editorial-policy`で" not in spec
