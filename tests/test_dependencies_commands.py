import json

from repo_context_map.commands import infer_commands
from repo_context_map.dependencies import summarize_dependencies

from conftest import write


def test_pyproject_dependencies(make_repo):
    summaries = summarize_dependencies(make_repo)
    python = summaries[0]
    assert python.ecosystem == "Python"
    assert "click" in python.dependencies
    assert "pytest" in python.dev_dependencies


def test_package_json_dependencies_and_commands(tmp_path):
    root = tmp_path / "node"
    write(
        root / "package.json",
        json.dumps(
            {
                "dependencies": {"react": "1.0.0"},
                "devDependencies": {"vitest": "1.0.0"},
                "scripts": {"test": "vitest", "dev": "vite", "lint": "eslint ."},
            }
        ),
    )
    summaries = summarize_dependencies(root)
    commands = infer_commands(root)
    assert summaries[0].ecosystem == "Node"
    assert "react" in summaries[0].dependencies
    assert "npm test" in commands["test"]
    assert "npm run dev" in commands["start"]


def test_go_and_cargo_commands(tmp_path):
    root = tmp_path / "multi"
    write(root / "go.mod", "module github.com/yanqr213/repo-context-map/examples/demo\nrequire golang.org/x/text v0.1.0\n")
    write(root / "Cargo.toml", "[dependencies]\nserde = \"1\"\n[dev-dependencies]\ninsta = \"1\"\n")
    summaries = summarize_dependencies(root)
    commands = infer_commands(root)
    assert {item.ecosystem for item in summaries} == {"Go", "Rust"}
    assert "go test ./..." in commands["test"]
    assert "cargo test" in commands["test"]
