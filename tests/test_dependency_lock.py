from pathlib import Path

import pytest
import yaml

from scripts import lock_requirements


@pytest.mark.parametrize("change", ["version", "marker", "index"])
def test_stale_lock_fails_without_modifying_files(tmp_path, monkeypatch, change) -> None:
    old = (
        "--index-url https://pypi.org/simple\nruff==0.16.1\n"
        "torch==2.8.0 ; sys_platform != 'linux'\n"
    )
    changes = {
        "version": old.replace("ruff==0.16.1", "ruff==0.17.2"),
        "marker": old.replace("!= 'linux'", "== 'linux'"),
        "index": old.replace("pypi.org", "example.org"),
    }
    path = tmp_path / "requirements.lock"
    path.write_text(old)
    monkeypatch.setattr(lock_requirements, "compile_lock", lambda _: changes[change])
    assert lock_requirements.update_lock(tmp_path, check=True) == 1
    assert path.read_text() == old
    assert lock_requirements.update_lock(tmp_path, check=False) == 0
    assert path.read_text() == changes[change]
    assert lock_requirements.update_lock(tmp_path, check=True) == 0


def test_lock_check_ignores_only_comments_and_blank_lines(tmp_path, monkeypatch) -> None:
    (tmp_path / "requirements.lock").write_text("# old generator\nruff==0.16.1\n")
    monkeypatch.setattr(
        lock_requirements, "compile_lock", lambda _: "ruff==0.16.1\n # via input\n\n"
    )
    assert lock_requirements.update_lock(tmp_path, check=True) == 0


@pytest.mark.parametrize("workflow,job", [("ci.yml", "test"), ("daily-news.yml", "update")])
def test_workflows_verify_before_installing_and_report_actual_versions(workflow, job) -> None:
    root = Path(__file__).resolve().parents[1]
    data = yaml.safe_load((root / ".github/workflows" / workflow).read_text())
    steps = data["jobs"][job]["steps"]
    commands = [step.get("run", "") for step in steps]
    verify = next(i for i, run in enumerate(commands) if "lock_requirements.py --check" in run)
    install = next(i for i, run in enumerate(commands) if "install -r requirements.lock" in run)
    assert verify < install
    assert f"uv=={lock_requirements.UV_VERSION}" in commands[verify]
    assert "pip check" in commands[install]
    assert "pip list --format=freeze" in commands[install]
