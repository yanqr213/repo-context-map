from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, Iterable, List

from .models import DependencySummary, FileInfo, RepoMap, TaskMarker


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
    _task_markers(lines, repo_map.task_markers)
    _risk_files(lines, repo_map.risk_files)
    _context_pack(lines, repo_map.context_pack)
    _list(lines, "Repository Risks", repo_map.risks)
    if repo_map.mermaid:
        lines.extend(["## Mermaid Dependency Graph", "", "```mermaid", repo_map.mermaid, "```", ""])
    return "\n".join(lines).rstrip() + "\n"


def to_agent_brief(repo_map: RepoMap) -> str:
    """Render a compact handoff brief that can be pasted into coding agents."""
    lines: List[str] = [
        "# Agent Repository Brief",
        "",
        "Use this brief to orient before making changes. Treat it as a map, then inspect the referenced files before editing.",
        "",
        "## Repository Snapshot",
        "",
        f"- Root: `{repo_map.root}`",
        f"- Files scanned: {repo_map.files_scanned}",
        f"- Files skipped: {repo_map.files_skipped}",
        f"- Main languages: {_language_summary(repo_map.language_stats)}",
        f"- Primary directory roles: {_role_summary(repo_map.role_stats)}",
        "",
    ]
    _brief_list(lines, "Start Here", _start_here(repo_map))
    _brief_commands(lines, repo_map.command_candidates)
    _brief_dependencies(lines, repo_map.dependencies)
    _brief_context_pack(lines, repo_map.context_pack)
    _brief_hotspots(lines, repo_map.hotspots)
    _brief_task_markers(lines, repo_map.task_markers)
    _brief_risks(lines, repo_map)
    lines.extend(
        [
            "## Suggested Agent Workflow",
            "",
            "1. Read the Start Here files and any files in the Recommended Context Pack that match the task.",
            "2. Confirm the relevant test, lint, or start command before changing code.",
            "3. Inspect risk files before copying repository context into chats, issues, or external tools.",
            "4. Keep edits scoped to the requested task and update tests or docs when behavior changes.",
            "",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def to_agent_prompt(repo_map: RepoMap, task: str = "") -> str:
    """Render a copy-ready kickoff prompt for AI coding agents."""

    task_text = task.strip() or "Describe the requested change here before sending this prompt to the agent."
    lines: List[str] = [
        "# Agent Kickoff Prompt",
        "",
        "You are working in the local repository described below. Use this as orientation, then inspect live files before editing.",
        "",
        "## Task",
        "",
        task_text,
        "",
        "## Repository Map",
        "",
        f"- Root: `{repo_map.root}`",
        f"- Files scanned: {repo_map.files_scanned}",
        f"- Main languages: {_language_summary(repo_map.language_stats)}",
        f"- Primary roles: {_role_summary(repo_map.role_stats)}",
        "",
    ]
    _prompt_section(lines, "Read First", _start_here(repo_map))
    _prompt_section(
        lines,
        "Recommended Context Files",
        [
            f"`{item['path']}` - {item['reason']} (~{item['estimated_tokens']} tokens)"
            for item in repo_map.context_pack[:12]
        ],
    )
    _prompt_commands(lines, repo_map.command_candidates)
    _prompt_section(
        lines,
        "Recent Hotspots",
        [f"`{item['path']}` - {item['changes']} recent changes" for item in repo_map.hotspots[:8]],
    )
    _prompt_section(
        lines,
        "Open Task Markers",
        [f"`{item.path}:{item.line}` - {item.tag}: {item.text}" for item in repo_map.task_markers[:8]],
    )
    risks = list(repo_map.risks[:8])
    risks.extend(f"`{item['path']}` - {', '.join(item['reasons'])}" for item in repo_map.risk_files[:8])
    _prompt_section(lines, "Risks And Guardrails", risks)
    lines.extend(
        [
            "## Working Rules",
            "",
            "- Read the relevant files before changing code; this map is a guide, not source of truth.",
            "- Keep edits scoped to the task and preserve existing project style.",
            "- Run the most relevant tests or checks listed above, then summarize evidence in the final response.",
            "- Do not paste secrets, private keys, or large generated artifacts into chat context.",
            "",
            "## Expected Final Response",
            "",
            "- What changed and why.",
            "- Files touched.",
            "- Tests or checks run, including failures if any.",
            "- Remaining risks or follow-up work.",
            "",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def to_manifest(repo_map: RepoMap) -> str:
    """Render the recommended context pack as a newline-delimited manifest."""

    paths = [str(item["path"]) for item in repo_map.context_pack if item.get("path")]
    return "\n".join(_dedupe(paths)) + ("\n" if paths else "")


def to_context_bundle(repo_map: RepoMap) -> str:
    """Render a paste-ready Markdown context bundle from recommended files."""

    root = Path(repo_map.root)
    lines: List[str] = [
        "# Repository Context Bundle",
        "",
        f"Root: `{repo_map.root}`",
        f"Files included: {len(repo_map.context_pack)}",
        "",
        "Use this bundle as initial AI coding context. Inspect the live files before editing.",
        "",
    ]
    for item in repo_map.context_pack:
        path = str(item.get("path") or "")
        if not path:
            continue
        full_path = (root / path).resolve()
        if not _is_within(root, full_path) or not full_path.is_file():
            continue
        text = full_path.read_text(encoding="utf-8", errors="replace")
        language = _fence_language(path)
        marker = _fence_marker(text)
        fence = f"{marker}{language} {path}".rstrip()
        lines.extend(
            [
                f"## file: {path}",
                "",
                f"- Reason: {item.get('reason', 'recommended context')}",
                f"- Estimated tokens: {item.get('estimated_tokens', 'unknown')}",
                "",
                fence,
                text.rstrip(),
                marker,
                "",
            ]
        )
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


def _task_markers(lines: List[str], task_markers: List[TaskMarker]) -> None:
    rows = [[item.path, item.line, item.tag, item.text] for item in task_markers]
    _table(lines, "Task Markers", ["Path", "Line", "Tag", "Text"], rows)


def _risk_files(lines: List[str], risk_files: List[Dict[str, Any]]) -> None:
    rows = [[item["path"], ", ".join(item["reasons"]), item["size"], item["complexity"]] for item in risk_files]
    _table(lines, "Risk Files", ["Path", "Reasons", "Bytes", "Complexity"], rows)


def _context_pack(lines: List[str], context_pack: List[Dict[str, Any]]) -> None:
    rows = [[item["path"], item["reason"], item["estimated_tokens"], item["score"]] for item in context_pack]
    _table(lines, "Recommended AI Context Pack", ["Path", "Reason", "Estimated Tokens", "Score"], rows)


def _language_summary(stats: Dict[str, Dict[str, int]]) -> str:
    if not stats:
        return "unknown"
    ordered = sorted(stats.items(), key=lambda item: (-item[1].get("files", 0), item[0]))
    return ", ".join(f"{name} ({_file_count(data.get('files', 0))})" for name, data in ordered[:5])


def _role_summary(stats: Dict[str, Dict[str, int]]) -> str:
    if not stats:
        return "unknown"
    ordered = sorted(stats.items(), key=lambda item: (-item[1].get("files", 0), item[0]))
    return ", ".join(f"{name} ({_file_count(data.get('files', 0))})" for name, data in ordered[:5])


def _file_count(count: int) -> str:
    return f"{count} file" if count == 1 else f"{count} files"


def _start_here(repo_map: RepoMap) -> List[str]:
    values: List[str] = []
    for path in repo_map.docs[:5]:
        values.append(f"`{path}` - documentation")
    for path in repo_map.entry_points[:8]:
        values.append(f"`{path}` - probable entry point")
    return _dedupe(values)[:12]


def _brief_list(lines: List[str], title: str, values: List[str]) -> None:
    lines.extend([f"## {title}", ""])
    if not values:
        lines.extend(["- No strong signal detected.", ""])
        return
    lines.extend(f"- {value}" for value in values)
    lines.append("")


def _brief_commands(lines: List[str], commands: Dict[str, List[str]]) -> None:
    lines.extend(["## Commands To Try", ""])
    labels = [("test", "Tests"), ("lint", "Lint"), ("format", "Format"), ("start", "Start or dev server")]
    emitted = False
    for key, label in labels:
        values = commands.get(key, [])
        if values:
            lines.append(f"- {label}: " + "; ".join(f"`{value}`" for value in values[:5]))
            emitted = True
    if not emitted:
        lines.append("- No command candidates detected. Inspect project manifests before running commands.")
    lines.append("")


def _brief_dependencies(lines: List[str], dependencies: List[DependencySummary]) -> None:
    lines.extend(["## Dependency Manifests", ""])
    if not dependencies:
        lines.extend(["- No dependency manifests detected.", ""])
        return
    for summary in dependencies[:10]:
        deps = ", ".join(summary.dependencies[:8]) or "none"
        dev = ", ".join(summary.dev_dependencies[:8]) or "none"
        lines.append(f"- `{summary.manifest}` ({summary.ecosystem}): runtime: {deps}; dev/test: {dev}")
    lines.append("")


def _brief_context_pack(lines: List[str], context_pack: List[Dict[str, Any]]) -> None:
    lines.extend(["## Recommended Context Pack", ""])
    if not context_pack:
        lines.extend(["- No context pack files selected within the configured budget.", ""])
        return
    for item in context_pack[:15]:
        lines.append(
            f"- `{item['path']}` - {item['reason']} (~{item['estimated_tokens']} tokens, score {item['score']})"
        )
    lines.append("")


def _brief_hotspots(lines: List[str], hotspots: List[Dict[str, Any]]) -> None:
    lines.extend(["## Recent Change Hotspots", ""])
    if not hotspots:
        lines.extend(["- No Git hotspot data detected.", ""])
        return
    for item in hotspots[:10]:
        lines.append(f"- `{item['path']}` - {item['changes']} recent changes")
    lines.append("")


def _brief_task_markers(lines: List[str], task_markers: List[TaskMarker]) -> None:
    lines.extend(["## Task Markers", ""])
    if not task_markers:
        lines.extend(["- No TODO/FIXME-style task markers detected.", ""])
        return
    for item in task_markers[:12]:
        lines.append(f"- `{item.path}:{item.line}` - {item.tag}: {item.text}")
    lines.append("")


def _brief_risks(lines: List[str], repo_map: RepoMap) -> None:
    lines.extend(["## Risks To Check Before Editing", ""])
    if not repo_map.risks and not repo_map.risk_files:
        lines.extend(["- No repository-level risks detected by the lightweight scanner.", ""])
        return
    for risk in repo_map.risks[:10]:
        lines.append(f"- {risk}")
    for item in repo_map.risk_files[:10]:
        lines.append(f"- `{item['path']}` - {', '.join(item['reasons'])}")
    lines.append("")


def _prompt_section(lines: List[str], title: str, values: List[str]) -> None:
    lines.extend([f"## {title}", ""])
    if values:
        lines.extend(f"- {value}" for value in values)
    else:
        lines.append("- No strong signal detected.")
    lines.append("")


def _prompt_commands(lines: List[str], commands: Dict[str, List[str]]) -> None:
    values: List[str] = []
    for key, label in [("test", "Test"), ("lint", "Lint"), ("format", "Format"), ("start", "Start")]:
        for command in commands.get(key, [])[:4]:
            values.append(f"{label}: `{command}`")
    _prompt_section(lines, "Commands To Verify", values)


def _dedupe(values: List[str]) -> List[str]:
    seen = set()
    result: List[str] = []
    for value in values:
        if value in seen:
            continue
        result.append(value)
        seen.add(value)
    return result


def _cell(value: Any) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def _is_within(root: Path, path: Path) -> bool:
    try:
        path.relative_to(root.resolve())
        return True
    except ValueError:
        return False


def _fence_marker(text: str) -> str:
    longest = 0
    current = 0
    for char in text:
        if char == "`":
            current += 1
            longest = max(longest, current)
        else:
            current = 0
    return "`" * max(3, longest + 1)


def _fence_language(path: str) -> str:
    suffix = Path(path).suffix.lower()
    return {
        ".py": "python",
        ".js": "javascript",
        ".jsx": "jsx",
        ".ts": "typescript",
        ".tsx": "tsx",
        ".json": "json",
        ".md": "markdown",
        ".yml": "yaml",
        ".yaml": "yaml",
        ".toml": "toml",
        ".rs": "rust",
        ".go": "go",
        ".java": "java",
        ".sh": "bash",
        ".ps1": "powershell",
    }.get(suffix, "")
