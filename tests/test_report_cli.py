import json

from repo_context_map.cli import main
from repo_context_map.models import ScanConfig
from repo_context_map.report import to_json, to_markdown, write_report
from repo_context_map.scanner import scan_repository

from conftest import write


def test_markdown_report_contains_sections(make_repo):
    repo_map = scan_repository(ScanConfig(root=make_repo, include_mermaid=True))
    markdown = to_markdown(repo_map)
    assert "# Repository Context Map" in markdown
    assert "## Recommended AI Context Pack" in markdown
    assert "```mermaid" in markdown


def test_json_report_is_parseable(make_repo):
    repo_map = scan_repository(ScanConfig(root=make_repo))
    data = json.loads(to_json(repo_map))
    assert data["files_scanned"] >= 4
    assert data["language_stats"]["Python"]["files"] >= 2


def test_write_report_creates_parent_directory(tmp_path, make_repo):
    repo_map = scan_repository(ScanConfig(root=make_repo))
    output = tmp_path / "nested" / "context.md"
    write_report(to_markdown(repo_map), str(output))
    assert output.exists()


def test_cli_scan_markdown_output(tmp_path, make_repo):
    output = tmp_path / "out" / "map.md"
    code = main(["scan", str(make_repo), "--output", str(output)])
    assert code == 0
    assert "Repository Context Map" in output.read_text(encoding="utf-8")


def test_cli_scan_json_stdout(capsys, make_repo):
    code = main(["scan", str(make_repo), "--format", "json"])
    captured = capsys.readouterr()
    assert code == 0
    assert json.loads(captured.out)["root"] == str(make_repo.resolve())


def test_cli_check_returns_nonzero_for_risky_repo(tmp_path, capsys):
    root = tmp_path / "risky"
    write(root / "src" / "app.py", "print('hi')\n")
    code = main(["scan", str(root), "--check"])
    captured = capsys.readouterr()
    assert code == 1
    assert "check:" in captured.err
