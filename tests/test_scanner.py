from repo_context_map.config import build_scan_config
from repo_context_map.models import ScanConfig
from repo_context_map.scanner import scan_repository

from conftest import write


def test_scan_repository_collects_core_sections(make_repo):
    repo_map = scan_repository(ScanConfig(root=make_repo))
    assert repo_map.files_scanned >= 4
    assert repo_map.language_stats["Python"]["files"] >= 2
    assert "README.md" in repo_map.docs
    assert "src/demo/cli.py" in repo_map.entry_points
    assert repo_map.command_candidates["test"]
    assert repo_map.context_pack


def test_scan_skips_binary_and_large_files(tmp_path):
    root = tmp_path / "repo"
    write(root / "README.md", "# Demo\n")
    (root / "image.bin").write_bytes(b"\0\1\2")
    write(root / "large.txt", "x" * 50)
    repo_map = scan_repository(ScanConfig(root=root, max_file_size=10))
    assert repo_map.files_skipped == 2
    assert repo_map.files_scanned == 1


def test_gitignore_is_applied(tmp_path):
    root = tmp_path / "repo"
    write(root / ".gitignore", "ignored/\n")
    write(root / "README.md", "# Demo\n")
    write(root / "ignored" / "hidden.py", "print('hidden')\n")
    repo_map = scan_repository(ScanConfig(root=root))
    assert all("ignored/hidden.py" != doc for doc in repo_map.docs)
    assert repo_map.files_skipped == 1


def test_risks_include_missing_tests_and_docs(tmp_path):
    root = tmp_path / "repo"
    write(root / "src" / "app.py", "print('hi')\n")
    repo_map = scan_repository(ScanConfig(root=root))
    assert any("No documentation" in risk for risk in repo_map.risks)
    assert any("No test" in risk for risk in repo_map.risks)


def test_config_json_overrides_budget(tmp_path):
    root = tmp_path / "repo"
    write(root / "README.md", "x" * 1000)
    write(root / "repo-context-map.json", '{"budget": 10, "ignore": ["skip.py"]}')
    write(root / "skip.py", "print('skip')\n")
    config = build_scan_config(str(root), config_path="repo-context-map.json")
    repo_map = scan_repository(config)
    assert config.budget == 10
    assert "skip.py" not in [item["path"] for item in repo_map.context_pack]
