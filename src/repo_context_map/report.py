from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, Iterable, List

from .models import DependencySummary, FileInfo, RepoMap


def to_json(repo_map: RepoMap) -> str:
    return json.dumps(asdict(repo_map), ensure_ascii=False, indent=2) + "\n"


def to_markdown(repo_map: RepoMap) -> str:
    lines: List[str] = [
        "# Repository Context Map",
        "",
        f"- Root: `{repo_map.root}`",
        f"- Files scanned: {repo_map.files_scanned}",
        f"- Files skipped: {repo_map.files_skipped}",
        f"- Total bytes scanned: {repo_map.total_bytes}",
        "",
    ]
    _table(lines, "Language Distribution", ["Language", "Files", "Lines", "Bytes"], _stats_rows(repo_map.language_stats))
    _table(lines, "Directory Roles", ["Directory", "Role"], sorted(repo_map.directory_roles.items())[:40])
    _list(lines, "Entry Points", repo_map.entry_points)
    _dependencies(lines, repo_map.dependencies)
    _commands(lines, repo_map.command_candidates)
    _list(lines, "Documentation Index", repo_map.docs)
    _files(lines, "Largest Files", repo_map.largest_files)
    _files(lines, "Most Complex Files", repo_map.complex_files)
    _hotspots(lines, repo_map.hotspots)
    _risk_files(lines, repo_map.risk_files)
    _context_pack(lines, repo_map.context_pack)
    _list(lines, "Repository Risks", repo_map.risks)
    if repo_map.mermaid:
        lines.extend(["## Mermaid Dependency Graph", "", "```mermaid", repo_map.mermaid, "```", ""])
    return "\n".join(lines).rstrip() + "\n"


def write_report(content: str, output: str) -> None:
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _stats_rows(stats: Dict[str, Dict[str, int]]) -> List[List[Any]]:
    return [[name, data.get("files", 0), data.get("lines", 0), data.get("bytes", 0)] for name, data in stats.items()]


def _table(lines: List[str], title: str, headers: List[str], rows: Iterable[Iterable[Any]]) -> None:
    rows = list(rows)
    lines.extend([f"## {title}", ""])
    if not rows:
        lines.extend(["No data detected.", ""])
        return
    lines.append("| " + " | ".join(headers) + " |")
    lines.append("| " + " | ".join(["---"] * len(headers)) + " |")
    for row in rows:
        lines.append("| " + " | ".join(_cell(value) for value in row) + " |")
    lines.append("")


def _list(lines: List[str], title: str, values: List[str]) -> None:
    lines.extend([f"## {title}", ""])
    if not values:
        lines.extend(["No data detected.", ""])
        return
    lines.extend(f"- `{value}`" for value in values[:30])
    lines.append("")


def _dependencies(lines: List[str], dependencies: List[DependencySummary]) -> None:
    lines.extend(["## Dependency Summary", ""])
    if not dependencies:
        lines.extend(["No dependency manifests detected.", ""])
        return
    for summary in dependencies:
        deps = ", ".join(summary.dependencies[:15]) or "none"
        dev = ", ".join(summary.dev_dependencies[:15]) or "none"
        lines.append(f"- `{summary.manifest}` ({summary.ecosystem}): dependencies: {deps}; dev: {dev}")
    lines.append("")


def _commands(lines: List[str], commands: Dict[str, List[str]]) -> None:
    lines.extend(["## Command Candidates", ""])
    for category, values in commands.items():
        if values:
            lines.append(f"- {category}: " + "; ".join(f"`{value}`" for value in values))
    if all(not values for values in commands.values()):
        lines.append("No command candidates detected.")
    lines.append("")


def _files(lines: List[str], title: str, files: List[FileInfo]) -> None:
    rows = [[item.path, item.language, item.line_count, item.size, item.complexity] for item in files]
    _table(lines, title, ["Path", "Language", "Lines", "Bytes", "Complexity"], rows)


def _hotspots(lines: List[str], hotspots: List[Dict[str, Any]]) -> None:
    _table(lines, "Recent Change Hotspots", ["Path", "Changes"], [[item["path"], item["changes"]] for item in hotspots])


def _risk_files(lines: List[str], risk_files: List[Dict[str, Any]]) -> None:
    rows = [[item["path"], ", ".join(item["reasons"]), item["size"], item["complexity"]] for item in risk_files]
    _table(lines, "Risk Files", ["Path", "Reasons", "Bytes", "Complexity"], rows)


def _context_pack(lines: List[str], context_pack: List[Dict[str, Any]]) -> None:
    rows = [[item["path"], item["reason"], item["estimated_tokens"], item["score"]] for item in context_pack]
    _table(lines, "Recommended AI Context Pack", ["Path", "Reason", "Estimated Tokens", "Score"], rows)


def _cell(value: Any) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")
