import json
import subprocess
import sys

from repo_context_map.cli import main
from repo_context_map.models import ScanConfig
from repo_context_map.report import to_agent_brief, to_context_bundle, to_json, to_manifest, to_markdown, write_report
from repo_context_map.scanner import scan_repository

from conftest import write


def test_markdown_report_contains_sections(make_repo):
    repo_map = scan_repository(ScanConfig(root=make_repo, include_mermaid=True))
    markdown = to_markdown(repo_map)
    assert "# Repository Context Map" in markdown
    assert "## Recommended AI Context Pack" in markdown
    assert "## Task Markers" in markdown
    assert "```mermaid" in markdown


def test_json_report_is_parseable(make_repo):
    repo_map = scan_repository(ScanConfig(root=make_repo))
    data = json.loads(to_json(repo_map))
    assert data["files_scanned"] >= 4
    assert data["language_stats"]["Python"]["files"] >= 2
    assert "task_markers" in data


def test_agent_brief_is_paste_ready(make_repo):
    repo_map = scan_repository(ScanConfig(root=make_repo))
    brief = to_agent_brief(repo_map)

    assert "# Agent Repository Brief" in brief
    assert "## Start Here" in brief
    assert "`README.md` - documentation" in brief
    assert "`src/demo/cli.py` - probable entry point" in brief
    assert "python -m pytest" in brief
    assert "## Task Markers" in brief
    assert "TODO: handle command errors" in brief
    assert "## Suggested Agent Workflow" in brief


def test_manifest_lists_recommended_context_paths(make_repo):
    repo_map = scan_repository(ScanConfig(root=make_repo))
    manifest = to_manifest(repo_map)

    assert "README.md" in manifest.splitlines()
    assert "src/demo/cli.py" in manifest.splitlines()


def test_context_bundle_contains_file_blocks(make_repo):
    repo_map = scan_repository(ScanConfig(root=make_repo))
    bundle = to_context_bundle(repo_map)

    assert "# Repository Context Bundle" in bundle
    assert "## file: README.md" in bundle
    assert "```markdown README.md" in bundle or "````markdown README.md" in bundle
    assert "## file: src/demo/cli.py" in bundle
    assert "```python src/demo/cli.py" in bundle
    assert "``\\`" not in bundle


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


def test_cli_scan_agent_brief_output(tmp_path, make_repo):
    output = tmp_path / "out" / "AGENT_BRIEF.md"
    code = main(["scan", str(make_repo), "--format", "agent-brief", "--output", str(output)])

    assert code == 0
    text = output.read_text(encoding="utf-8")
    assert "Agent Repository Brief" in text
    assert "Recommended Context Pack" in text


def test_cli_scan_manifest_and_context_bundle_outputs(tmp_path, make_repo):
    manifest = tmp_path / "out" / "context-manifest.txt"
    bundle = tmp_path / "out" / "context-bundle.md"

    manifest_code = main(["scan", str(make_repo), "--format", "manifest", "--output", str(manifest)])
    bundle_code = main(["scan", str(make_repo), "--format", "context-bundle", "--output", str(bundle)])

    assert manifest_code == 0
    assert bundle_code == 0
    assert "README.md" in manifest.read_text(encoding="utf-8")
    assert "# Repository Context Bundle" in bundle.read_text(encoding="utf-8")


def test_python_module_entrypoint_reports_version():
    completed = subprocess.run(
        [sys.executable, "-m", "repo_context_map", "--version"],
        check=True,
        capture_output=True,
        text=True,
    )

    assert "repo-context-map 0.4.0" in completed.stdout


def test_cli_check_returns_nonzero_for_risky_repo(tmp_path, capsys):
    root = tmp_path / "risky"
    write(root / "src" / "app.py", "print('hi')\n")
    code = main(["scan", str(root), "--check"])
    captured = capsys.readouterr()
    assert code == 1
    assert "check:" in captured.err
