from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_about_exposes_editorial_and_correction_policy() -> None:
    about = (ROOT / "src/pages/about.astro").read_text(encoding="utf-8")

    assert 'id="editorial-policy"' in about
    for phrase in (
        "RSS/Atom由来",
        "元記事ページのHTMLをスクレイピングせず",
        "自動収集、自動翻訳、定型編集",
        "原文にない評価、影響、推測、将来予測",
        "原題表示や公式リンク案内へフォールバック",
        "記事URL、公式発表URL、誤りの箇所",
        "公式発表の更新や撤回",
        "人間確認済みの解説・コラムは現在提供していません",
    ):
        assert phrase in about


def test_editorial_policy_is_reachable_from_shared_footer() -> None:
    layout = (ROOT / "src/layouts/BaseLayout.astro").read_text(encoding="utf-8")

    assert 'href="/about/#editorial-policy"' in layout
