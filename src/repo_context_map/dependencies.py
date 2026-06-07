from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover
    tomllib = None  # type: ignore

from .models import DependencySummary


def summarize_dependencies(root: Path) -> List[DependencySummary]:
    summaries: List[DependencySummary] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(root).as_posix()
        if path.name == "pyproject.toml":
            summaries.append(_from_pyproject(path, rel))
        elif path.name == "requirements.txt":
            summaries.append(_from_requirements(path, rel))
        elif path.name == "package.json":
            summaries.append(_from_package_json(path, rel))
        elif path.name == "go.mod":
            summaries.append(_from_go_mod(path, rel))
        elif path.name == "Cargo.toml":
            summaries.append(_from_cargo(path, rel))
    return [item for item in summaries if item.dependencies or item.dev_dependencies or item.manifest]


def _from_pyproject(path: Path, rel: str) -> DependencySummary:
    data = _read_toml(path)
    project = data.get("project", {}) if isinstance(data, dict) else {}
    dependencies = _names(project.get("dependencies", []))
    optional = project.get("optional-dependencies", {})
    dev_dependencies: List[str] = []
    if isinstance(optional, dict):
        for group, deps in optional.items():
            if group in {"dev", "test", "docs", "lint"}:
                dev_dependencies.extend(_names(deps))
    poetry = data.get("tool", {}).get("poetry", {}) if isinstance(data.get("tool"), dict) else {}
    if isinstance(poetry, dict):
        dependencies.extend([name for name in poetry.get("dependencies", {}) if name.lower() != "python"])
        dev_dependencies.extend(list(poetry.get("group", {}).get("dev", {}).get("dependencies", {}).keys()))
    return DependencySummary("Python", rel, sorted(set(dependencies)), sorted(set(dev_dependencies)))


def _from_requirements(path: Path, rel: str) -> DependencySummary:
    deps: List[str] = []
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("-"):
            continue
        deps.append(re.split(r"[<>=!~\[]", line, maxsplit=1)[0].strip())
    return DependencySummary("Python", rel, sorted(set(deps)), [])


def _from_package_json(path: Path, rel: str) -> DependencySummary:
    data = json.loads(path.read_text(encoding="utf-8"))
    return DependencySummary(
        "Node",
        rel,
        sorted((data.get("dependencies") or {}).keys()),
        sorted((data.get("devDependencies") or {}).keys()),
    )


def _from_go_mod(path: Path, rel: str) -> DependencySummary:
    deps: List[str] = []
    in_block = False
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        stripped = line.strip()
        if stripped.startswith("require ("):
            in_block = True
            continue
        if in_block and stripped == ")":
            in_block = False
            continue
        if stripped.startswith("require "):
            parts = stripped.split()
            if len(parts) >= 2:
                deps.append(parts[1])
        elif in_block and stripped:
            deps.append(stripped.split()[0])
    return DependencySummary("Go", rel, sorted(set(deps)), [])


def _from_cargo(path: Path, rel: str) -> DependencySummary:
    data = _read_toml(path)
    deps = _table_keys(data.get("dependencies", {}))
    dev = _table_keys(data.get("dev-dependencies", {}))
    return DependencySummary("Rust", rel, sorted(deps), sorted(dev))


def _read_toml(path: Path) -> Dict[str, Any]:
    if tomllib is None:  # pragma: no cover
        return _read_simple_toml(path)
    with path.open("rb") as fh:
        return tomllib.load(fh)


def _names(dependencies: Iterable[str]) -> List[str]:
    return [re.split(r"[<>=!~\[]", item, maxsplit=1)[0].strip() for item in dependencies if isinstance(item, str)]


def _table_keys(value: Any) -> List[str]:
    return list(value.keys()) if isinstance(value, dict) else []


def _read_simple_toml(path: Path) -> Dict[str, Any]:  # pragma: no cover
    data: Dict[str, Any] = {}
    section: List[str] = []
    for raw_line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("[") and line.endswith("]"):
            section = [part.strip() for part in line.strip("[]").split(".")]
            cursor = data
            for part in section:
                cursor = cursor.setdefault(part, {})
            continue
        if "=" not in line:
            continue
        key, value = [part.strip() for part in line.split("=", 1)]
        cursor = data
        for part in section:
            cursor = cursor.setdefault(part, {})
        if value.startswith("[") and value.endswith("]"):
            cursor[key] = [item.strip().strip('"').strip("'") for item in value.strip("[]").split(",") if item.strip()]
        elif value.startswith("{") and value.endswith("}"):
            cursor[key] = {}
        else:
            cursor[key] = value.strip('"').strip("'")
    return data
