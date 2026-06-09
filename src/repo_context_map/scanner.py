from __future__ import annotations

import os
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

from .classify import detect_language, infer_directory_role, infer_file_role, is_doc, is_entry_point
from .commands import infer_commands
from .dependencies import summarize_dependencies
from .gitinfo import collect_hotspots
from .ignore import IgnoreMatcher
from .models import FileInfo, RepoMap, ScanConfig, TaskMarker

BINARY_SAMPLE_SIZE = 4096
COMPLEXITY_KEYWORDS = re.compile(r"\b(if|elif|else|for|while|case|catch|except|and|or|match|switch)\b|&&|\|\||\?")
TASK_MARKER_PATTERN = re.compile(
    r"^\s*(?:#|//|/\*+|\*|<!--|;|--|rem\b|REM\b)\s*"
    r"\b(TODO|FIXME|XXX|HACK|BUG|OPTIMIZE)\b[:\-\s]*(.*)",
    re.IGNORECASE,
)
TASK_MARKER_LIMIT = 50
RISK_NAMES = {"secrets.json", ".env", ".env.local", "id_rsa", "id_dsa"}
RISK_SUFFIXES = {".pem", ".key", ".p12"}


def scan_repository(config: ScanConfig) -> RepoMap:
    root = config.root.resolve()
    matcher = IgnoreMatcher.from_root(root, config.ignore_patterns, config.include_gitignore)
    files: List[FileInfo] = []
    task_markers: List[TaskMarker] = []
    skipped = 0
    total_bytes = 0
    directory_roles: Dict[str, str] = {}

    for current_root, dir_names, file_names in os.walk(root):
        current = Path(current_root)
        rel_dir = _relative(root, current)
        if rel_dir:
            directory_roles[rel_dir] = infer_directory_role(rel_dir)
        kept_dirs = []
        for name in dir_names:
            child = current / name
            if matcher.ignores(_relative(root, child), is_dir=True):
                skipped += _count_files(child)
            else:
                kept_dirs.append(name)
        dir_names[:] = kept_dirs
        for file_name in file_names:
            path = current / file_name
            rel = _relative(root, path)
            if matcher.ignores(rel, is_dir=False):
                skipped += 1
                continue
            info, markers, was_skipped = _inspect_file(path, rel, config.max_file_size)
            if was_skipped:
                skipped += 1
            else:
                total_bytes += info.size
                if len(task_markers) < TASK_MARKER_LIMIT:
                    task_markers.extend(markers[: TASK_MARKER_LIMIT - len(task_markers)])
            files.append(info)

    language_stats = _stats(files, "language")
    role_stats = _stats(files, "role")
    dependencies = summarize_dependencies(root)
    commands = infer_commands(root)
    docs = sorted(info.path for info in files if is_doc(info.path) and not info.skipped_reason)
    entry_points = sorted(info.path for info in files if is_entry_point(info.path) and not info.skipped_reason)
    largest = sorted((f for f in files if not f.skipped_reason), key=lambda item: item.size, reverse=True)[:10]
    complex_files = sorted((f for f in files if not f.skipped_reason), key=lambda item: item.complexity, reverse=True)[:10]
    hotspots = collect_hotspots(root)
    risk_files = _risk_files(files)
    context_pack = _context_pack(files, docs, entry_points, hotspots, config.budget)
    risks = _repository_risks(docs, role_stats, commands, risk_files)
    mermaid = _mermaid_dependencies(dependencies) if config.include_mermaid else ""

    return RepoMap(
        root=str(root),
        files_scanned=sum(1 for item in files if not item.skipped_reason),
        files_skipped=skipped,
        total_bytes=total_bytes,
        language_stats=language_stats,
        role_stats=role_stats,
        directory_roles=directory_roles,
        dependencies=dependencies,
        command_candidates=commands,
        docs=docs,
        largest_files=largest,
        complex_files=complex_files,
        hotspots=hotspots,
        task_markers=task_markers,
        risk_files=risk_files,
        context_pack=context_pack,
        entry_points=entry_points,
        mermaid=mermaid,
        risks=risks,
    )


def _inspect_file(path: Path, rel: str, max_file_size: int) -> Tuple[FileInfo, List[TaskMarker], bool]:
    size = path.stat().st_size
    language = detect_language(rel)
    role = infer_file_role(rel)
    info = FileInfo(path=rel, size=size, language=language, role=role)
    if size > max_file_size:
        info.skipped_reason = "too_large"
        return info, [], True
    if _is_binary(path):
        info.is_binary = True
        info.skipped_reason = "binary"
        return info, [], True
    text = path.read_text(encoding="utf-8", errors="ignore")
    lines = text.splitlines()
    info.line_count = len(lines)
    info.complexity = _estimate_complexity(lines)
    return info, _task_markers(rel, lines), False


def _is_binary(path: Path) -> bool:
    sample = path.read_bytes()[:BINARY_SAMPLE_SIZE]
    return b"\0" in sample


def _estimate_complexity(lines: Iterable[str]) -> int:
    score = 0
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith(("#", "//", "/*", "*")):
            continue
        score += len(COMPLEXITY_KEYWORDS.findall(stripped))
    return score


def _task_markers(path: str, lines: List[str]) -> List[TaskMarker]:
    markers: List[TaskMarker] = []
    for line_number, line in enumerate(lines, start=1):
        match = TASK_MARKER_PATTERN.search(line)
        if not match:
            continue
        tag = match.group(1).upper()
        text = _clean_marker_text(match.group(2))
        markers.append(TaskMarker(path=path, line=line_number, tag=tag, text=text))
        if len(markers) >= 10:
            break
    return markers


def _clean_marker_text(text: str) -> str:
    cleaned = text.strip().removesuffix("-->").strip().strip("#/*-:; ")
    return cleaned[:160] if cleaned else "(no description)"


def _stats(files: List[FileInfo], attr: str) -> Dict[str, Dict[str, int]]:
    buckets: Dict[str, Counter] = defaultdict(Counter)
    for info in files:
        if info.skipped_reason:
            continue
        value = getattr(info, attr)
        buckets[value]["files"] += 1
        buckets[value]["bytes"] += info.size
        buckets[value]["lines"] += info.line_count
    return {key: dict(value) for key, value in sorted(buckets.items())}


def _risk_files(files: List[FileInfo]) -> List[Dict[str, object]]:
    risks: List[Dict[str, object]] = []
    for info in files:
        name = Path(info.path).name
        suffix = Path(info.path).suffix
        reasons: List[str] = []
        if name in RISK_NAMES or suffix in RISK_SUFFIXES:
            reasons.append("sensitive-looking filename")
        if info.size > 250_000 and not info.skipped_reason:
            reasons.append("large file")
        if info.complexity > 80:
            reasons.append("high estimated branching complexity")
        if reasons:
            risks.append({"path": info.path, "reasons": reasons, "size": info.size, "complexity": info.complexity})
    return risks[:20]


def _repository_risks(
    docs: List[str],
    role_stats: Dict[str, Dict[str, int]],
    commands: Dict[str, List[str]],
    risk_files: List[Dict[str, object]],
) -> List[str]:
    risks: List[str] = []
    if not docs:
        risks.append("No documentation files detected.")
    if "tests" not in role_stats:
        risks.append("No test files or test directories detected.")
    if not commands.get("test"):
        risks.append("No test command candidates detected.")
    if risk_files:
        risks.append("Risk files detected; review before sharing context.")
    return risks


def _context_pack(
    files: List[FileInfo],
    docs: List[str],
    entry_points: List[str],
    hotspots: List[Dict[str, object]],
    budget: int,
) -> List[Dict[str, object]]:
    priority: Dict[str, int] = {}
    for path in docs[:8]:
        priority[path] = max(priority.get(path, 0), 100)
    for path in entry_points[:8]:
        priority[path] = max(priority.get(path, 0), 90)
    for item in hotspots:
        priority[str(item["path"])] = max(priority.get(str(item["path"]), 0), 80 + int(item["changes"]))
    for info in files:
        if info.role in {"config", "tests"}:
            priority[info.path] = max(priority.get(info.path, 0), 40)
    by_path = {info.path: info for info in files if not info.skipped_reason}
    selected: List[Dict[str, object]] = []
    spent = 0
    for path, score in sorted(priority.items(), key=lambda item: (-item[1], item[0])):
        info = by_path.get(path)
        if not info:
            continue
        estimated_tokens = max(1, info.size // 4)
        if selected and spent + estimated_tokens > budget:
            continue
        selected.append(
            {
                "path": path,
                "reason": _context_reason(info, score),
                "estimated_tokens": estimated_tokens,
                "score": score,
            }
        )
        spent += estimated_tokens
        if spent >= budget:
            break
    return selected


def _context_reason(info: FileInfo, score: int) -> str:
    if score >= 100:
        return "key documentation"
    if score >= 90:
        return "probable entry point"
    if score >= 80:
        return "recent change hotspot"
    if info.role == "tests":
        return "test behavior reference"
    return "configuration or project shape"


def _mermaid_dependencies(dependencies: List[object]) -> str:
    lines = ["graph TD", '  repo["repository"]']
    for summary in dependencies:
        manifest_id = _node_id(summary.manifest)
        lines.append(f'  repo --> {manifest_id}["{summary.manifest}"]')
        for dep in (summary.dependencies + summary.dev_dependencies)[:12]:
            dep_id = _node_id(summary.manifest + dep)
            lines.append(f'  {manifest_id} --> {dep_id}["{dep}"]')
    return "\n".join(lines)


def _node_id(value: str) -> str:
    return "n" + re.sub(r"[^A-Za-z0-9_]", "_", value)


def _relative(root: Path, path: Path) -> str:
    return path.relative_to(root).as_posix() if path != root else ""


def _count_files(path: Path) -> int:
    return sum(1 for item in path.rglob("*") if item.is_file())
