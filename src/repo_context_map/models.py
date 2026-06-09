from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class FileInfo:
    path: str
    size: int
    language: str
    role: str
    line_count: int = 0
    complexity: int = 0
    is_binary: bool = False
    skipped_reason: Optional[str] = None


@dataclass
class DependencySummary:
    ecosystem: str
    manifest: str
    dependencies: List[str] = field(default_factory=list)
    dev_dependencies: List[str] = field(default_factory=list)


@dataclass
class TaskMarker:
    path: str
    line: int
    tag: str
    text: str


@dataclass
class ScanConfig:
    root: Path
    max_file_size: int = 512_000
    ignore_patterns: List[str] = field(default_factory=list)
    include_gitignore: bool = True
    include_mermaid: bool = False
    budget: int = 5000
    check: bool = False


@dataclass
class RepoMap:
    root: str
    files_scanned: int
    files_skipped: int
    total_bytes: int
    language_stats: Dict[str, Dict[str, int]]
    role_stats: Dict[str, Dict[str, int]]
    directory_roles: Dict[str, str]
    dependencies: List[DependencySummary]
    command_candidates: Dict[str, List[str]]
    docs: List[str]
    largest_files: List[FileInfo]
    complex_files: List[FileInfo]
    hotspots: List[Dict[str, Any]]
    task_markers: List[TaskMarker]
    risk_files: List[Dict[str, Any]]
    context_pack: List[Dict[str, Any]]
    entry_points: List[str]
    mermaid: str = ""
    risks: List[str] = field(default_factory=list)
