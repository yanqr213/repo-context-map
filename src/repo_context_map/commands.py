from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List


def infer_commands(root: Path) -> Dict[str, List[str]]:
    commands = {"test": [], "format": [], "lint": [], "start": []}
    if (root / "pyproject.toml").exists() or (root / "pytest.ini").exists() or (root / "tests").exists():
        commands["test"].append("python -m pytest")
    if (root / "pyproject.toml").exists():
        commands["format"].extend(["python -m black .", "python -m ruff format ."])
        commands["lint"].append("python -m ruff check .")
    package_json = root / "package.json"
    if package_json.exists():
        data = json.loads(package_json.read_text(encoding="utf-8"))
        scripts = data.get("scripts") or {}
        for key in scripts:
            if key in {"test", "format", "lint", "start", "dev", "build"}:
                bucket = "start" if key in {"start", "dev"} else key
                if bucket in commands:
                    commands[bucket].append(f"npm run {key}" if key not in {"start", "test"} else f"npm {key}")
    if (root / "go.mod").exists():
        commands["test"].append("go test ./...")
        commands["format"].append("gofmt -w .")
    if (root / "Cargo.toml").exists():
        commands["test"].append("cargo test")
        commands["format"].append("cargo fmt")
        commands["lint"].append("cargo clippy --all-targets --all-features")
        commands["start"].append("cargo run")
    if (root / "Makefile").exists():
        commands["test"].append("make test")
        commands["format"].append("make format")
        commands["lint"].append("make lint")
    return {key: _dedupe(value) for key, value in commands.items()}


def _dedupe(values: List[str]) -> List[str]:
    seen = set()
    result: List[str] = []
    for value in values:
        if value not in seen:
            result.append(value)
            seen.add(value)
    return result
