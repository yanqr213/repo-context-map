from __future__ import annotations

import fnmatch
from pathlib import Path
from typing import Iterable, List

from .classify import normalize_path


DEFAULT_IGNORES = [
    ".git/",
    ".hg/",
    ".svn/",
    "__pycache__/",
    ".pytest_cache/",
    ".mypy_cache/",
    ".ruff_cache/",
    ".venv/",
    "venv/",
    "node_modules/",
    "dist/",
    "build/",
    "target/",
    ".DS_Store",
]


class IgnoreMatcher:
    def __init__(self, patterns: Iterable[str]) -> None:
        self.patterns = [p.strip() for p in patterns if p and p.strip() and not p.lstrip().startswith("#")]

    @classmethod
    def from_root(cls, root: Path, extra_patterns: Iterable[str], include_gitignore: bool = True) -> "IgnoreMatcher":
        patterns: List[str] = list(DEFAULT_IGNORES)
        if include_gitignore:
            gitignore = root / ".gitignore"
            if gitignore.exists():
                patterns.extend(gitignore.read_text(encoding="utf-8", errors="ignore").splitlines())
        patterns.extend(extra_patterns)
        return cls(patterns)

    def ignores(self, relative_path: str, is_dir: bool = False) -> bool:
        path = normalize_path(relative_path).strip("/")
        ignored = False
        for raw_pattern in self.patterns:
            negate = raw_pattern.startswith("!")
            pattern = raw_pattern[1:] if negate else raw_pattern
            if self._matches(path, is_dir, pattern):
                ignored = not negate
        return ignored

    def _matches(self, path: str, is_dir: bool, pattern: str) -> bool:
        pattern = normalize_path(pattern).strip()
        if not pattern:
            return False
        directory_only = pattern.endswith("/")
        pattern = pattern.strip("/")
        if directory_only and not is_dir and not any(part == pattern for part in path.split("/")):
            return False
        if "/" not in pattern:
            if fnmatch.fnmatch(path, pattern):
                return True
            return any(fnmatch.fnmatch(part, pattern) for part in path.split("/"))
        return fnmatch.fnmatch(path, pattern) or fnmatch.fnmatch("/" + path, pattern)
