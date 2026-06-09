from __future__ import annotations

from pathlib import Path

import pytest


def write(path: Path, content: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


@pytest.fixture
def make_repo(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    write(root / "README.md", "# Demo\n")
    write(
        root / "pyproject.toml",
        "[project]\nname = \"demo\"\nversion = \"0.1.0\"\ndependencies = [\"click>=8\"]\n"
        "[project.optional-dependencies]\ndev = [\"pytest>=7\"]\n",
    )
    write(root / "src" / "demo" / "cli.py", "def main():\n    # TODO: handle command errors\n    if True:\n        return 0\n")
    write(root / "tests" / "test_cli.py", "def test_ok():\n    assert True\n")
    return root
