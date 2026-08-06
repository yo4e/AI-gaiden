from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
PRODUCTION_SITE_URL = "https://ai.gaiden.news"
OPERATOR_SITE_URL = "https://gaiden.news/"


def read_repository_file(path: str) -> str:
    return (REPOSITORY_ROOT / path).read_text(encoding="utf-8")


def test_production_domain_is_used_for_generated_absolute_urls() -> None:
    astro_config = read_repository_file("astro.config.mjs")
    ci_workflow = read_repository_file(".github/workflows/ci.yml")
    daily_workflow = read_repository_file(".github/workflows/daily-news.yml")
    site_constants = read_repository_file("src/lib/site.ts")

    assert f"const PRODUCTION_SITE_URL = '{PRODUCTION_SITE_URL}'" in astro_config
    assert f"SITE_URL: {PRODUCTION_SITE_URL}" in ci_workflow
    assert f"SITE_URL: {PRODUCTION_SITE_URL}" in daily_workflow
    assert f"export const SITE_URL = '{PRODUCTION_SITE_URL}'" in site_constants


def test_operator_site_replaces_the_legacy_embedded_page() -> None:
    site_constants = read_repository_file("src/lib/site.ts")
    base_layout = read_repository_file("src/layouts/BaseLayout.astro")
    about_page = read_repository_file("src/pages/about.astro")
    redirects = read_repository_file("public/_redirects")

    assert f"export const OPERATOR_URL = '{OPERATOR_SITE_URL}'" in site_constants
    assert "href={OPERATOR_URL}" in base_layout
    assert "href={OPERATOR_URL}" in about_page
    assert "/gaiden https://gaiden.news/ 301" in redirects
    assert not (REPOSITORY_ROOT / "src/pages/gaiden.astro").exists()


def test_domain_migration_is_recorded_in_project_documentation() -> None:
    readme = read_repository_file("README.md")
    implementation_spec = read_repository_file("docs/IMPLEMENTATION_SPEC.md")

    assert f"正式URL: <{PRODUCTION_SITE_URL}/>" in readme
    assert f"正式公開先: **{PRODUCTION_SITE_URL}/**" in implementation_spec
    assert "### 1.3 公開ドメイン" in implementation_spec
    assert "ai-gaiden.pages.dev" in implementation_spec
