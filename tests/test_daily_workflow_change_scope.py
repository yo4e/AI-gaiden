from __future__ import annotations

from pathlib import Path
import subprocess


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_PATH = REPOSITORY_ROOT / ".github" / "workflows" / "daily-news.yml"


def run_git(repository: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=repository,
        check=True,
        capture_output=True,
        text=True,
    )


def run_scope_check(repository: Path) -> subprocess.CompletedProcess[str]:
    script = r'''
invalid=0
while IFS= read -r path; do
  case "$path" in
    src/content/articles/*.md|src/content/articles/**/*.md|data/seen.json) ;;
    *)
      echo "Unexpected generated change: $path" >&2
      invalid=1
      ;;
  esac
done < <(git status --porcelain=v1 --untracked-files=all | cut -c4-)
exit "$invalid"
'''
    return subprocess.run(
        ["bash", "-c", script],
        cwd=repository,
        check=False,
        capture_output=True,
        text=True,
    )


def test_workflow_lists_untracked_files_individually() -> None:
    workflow = WORKFLOW_PATH.read_text(encoding="utf-8")

    assert "git status --short --untracked-files=all" in workflow
    assert "git status --porcelain=v1 --untracked-files=all | cut -c4-" in workflow


def test_new_article_directory_is_validated_by_file(tmp_path: Path) -> None:
    run_git(tmp_path, "init")
    article_dir = tmp_path / "src" / "content" / "articles" / "2026-08-06"
    article_dir.mkdir(parents=True)
    (article_dir / "first.md").write_text("first\n", encoding="utf-8")
    (article_dir / "second.md").write_text("second\n", encoding="utf-8")
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "seen.json").write_text("{}\n", encoding="utf-8")

    status = run_git(tmp_path, "status", "--porcelain=v1", "--untracked-files=all").stdout
    changed_paths = {line[3:] for line in status.splitlines()}

    assert "src/content/articles/2026-08-06/first.md" in changed_paths
    assert "src/content/articles/2026-08-06/second.md" in changed_paths
    assert "src/content/articles/2026-08-06/" not in changed_paths
    assert run_scope_check(tmp_path).returncode == 0


def test_unexpected_generated_file_is_still_rejected(tmp_path: Path) -> None:
    run_git(tmp_path, "init")
    unexpected = tmp_path / "unexpected.txt"
    unexpected.write_text("unexpected\n", encoding="utf-8")

    result = run_scope_check(tmp_path)

    assert result.returncode == 1
    assert "Unexpected generated change: unexpected.txt" in result.stderr
