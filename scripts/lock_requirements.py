"""Regenerate or verify the universal Python 3.12 lock without upgrading unrelated pins."""

from __future__ import annotations

import argparse
import difflib
import shutil
import subprocess
import tempfile
from pathlib import Path

UV_VERSION = "0.12.17"
ROOT = Path(__file__).resolve().parents[1]
COMPILE_COMMAND = [
    "uv",
    "pip",
    "compile",
    "--python-version",
    "3.12",
    "--universal",
    "--index-strategy",
    "unsafe-best-match",
    "--emit-index-url",
    "--custom-compile-command",
    "python scripts/lock_requirements.py",
    "requirements.in",
    "--output-file",
    "requirements.lock",
    "--quiet",
]


def lock_entries(text: str) -> list[str]:
    """Compare install instructions, including markers and indexes, not uv comments."""
    return [
        line.strip()
        for line in text.splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]


def compile_lock(root: Path) -> str:
    version = subprocess.run(["uv", "--version"], check=True, capture_output=True, text=True)
    if version.stdout.split()[1] != UV_VERSION:
        raise ValueError(f"Use uv=={UV_VERSION} to compile requirements.lock")
    with tempfile.TemporaryDirectory(prefix="ai-gaiden-lock-") as temporary:
        target = Path(temporary)
        shutil.copy2(root / "requirements.in", target / "requirements.in")
        # uv uses the existing output as version preferences, avoiding unrelated upgrades.
        if (root / "requirements.lock").exists():
            shutil.copy2(root / "requirements.lock", target / "requirements.lock")
        subprocess.run(COMPILE_COMMAND, cwd=target, check=True)
        return (target / "requirements.lock").read_text(encoding="utf-8")


def update_lock(root: Path, *, check: bool) -> int:
    path = root / "requirements.lock"
    expected = compile_lock(root)
    actual = path.read_text(encoding="utf-8") if path.exists() else ""
    if check:
        if lock_entries(actual) != lock_entries(expected):
            print("requirements.lock is stale. Run: python scripts/lock_requirements.py")
            print(
                "\n".join(
                    difflib.unified_diff(
                        lock_entries(actual),
                        lock_entries(expected),
                        fromfile="committed lock",
                        tofile="regenerated lock",
                        lineterm="",
                    )
                )
            )
            return 1
        print("requirements.in and requirements.lock are consistent.")
    else:
        path.write_text(expected, encoding="utf-8")
        print("Regenerated requirements.lock; commit it together with requirements.in.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Fail on drift; do not write files")
    args = parser.parse_args()
    try:
        return update_lock(ROOT, check=args.check)
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        print(f"Lock verification failed: {error}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
