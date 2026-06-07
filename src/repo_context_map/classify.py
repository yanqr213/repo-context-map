from __future__ import annotations

from pathlib import PurePosixPath
from typing import Dict


LANGUAGE_BY_NAME: Dict[str, str] = {
    "Dockerfile": "Dockerfile",
    "Makefile": "Makefile",
    "Gemfile": "Ruby",
    "Rakefile": "Ruby",
    "go.mod": "Go",
    "go.sum": "Go",
    "Cargo.toml": "Rust",
    "Cargo.lock": "Rust",
    "pyproject.toml": "Python",
    "requirements.txt": "Python",
    "package.json": "JavaScript",
    "package-lock.json": "JavaScript",
    "pnpm-lock.yaml": "JavaScript",
    "yarn.lock": "JavaScript",
}

LANGUAGE_BY_SUFFIX: Dict[str, str] = {
    ".py": "Python",
    ".js": "JavaScript",
    ".jsx": "JavaScript",
    ".mjs": "JavaScript",
    ".cjs": "JavaScript",
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
    ".go": "Go",
    ".rs": "Rust",
    ".java": "Java",
    ".kt": "Kotlin",
    ".kts": "Kotlin",
    ".rb": "Ruby",
    ".php": "PHP",
    ".cs": "C#",
    ".c": "C",
    ".h": "C/C++",
    ".cpp": "C++",
    ".cc": "C++",
    ".hpp": "C++",
    ".swift": "Swift",
    ".scala": "Scala",
    ".sh": "Shell",
    ".bash": "Shell",
    ".zsh": "Shell",
    ".ps1": "PowerShell",
    ".html": "HTML",
    ".css": "CSS",
    ".scss": "SCSS",
    ".json": "JSON",
    ".yaml": "YAML",
    ".yml": "YAML",
    ".toml": "TOML",
    ".md": "Markdown",
    ".rst": "reStructuredText",
    ".sql": "SQL",
    ".xml": "XML",
}

DOC_NAMES = {
    "README.md",
    "README.rst",
    "CHANGELOG.md",
    "CONTRIBUTING.md",
    "LICENSE",
    "SECURITY.md",
    "ARCHITECTURE.md",
}

ENTRY_NAMES = {
    "main.py",
    "app.py",
    "server.py",
    "cli.py",
    "index.js",
    "main.js",
    "server.js",
    "index.ts",
    "main.ts",
    "cmd/root.go",
    "src/main.rs",
}


def normalize_path(path: str) -> str:
    return path.replace("\\", "/")


def detect_language(path: str) -> str:
    posix = normalize_path(path)
    name = PurePosixPath(posix).name
    if name in LANGUAGE_BY_NAME:
        return LANGUAGE_BY_NAME[name]
    return LANGUAGE_BY_SUFFIX.get(PurePosixPath(posix).suffix.lower(), "Other")


def infer_file_role(path: str) -> str:
    posix = normalize_path(path)
    parts = set(PurePosixPath(posix).parts)
    name = PurePosixPath(posix).name
    lower_name = name.lower()
    if name in DOC_NAMES or lower_name.endswith((".md", ".rst")):
        return "docs"
    if "test" in parts or "tests" in parts or lower_name.startswith("test_") or lower_name.endswith("_test.py"):
        return "tests"
    if "examples" in parts or "sample" in parts or "samples" in parts:
        return "examples"
    if "scripts" in parts or "bin" in parts:
        return "scripts"
    if "docs" in parts:
        return "docs"
    if "src" in parts or "lib" in parts or "app" in parts:
        return "source"
    if "config" in parts or lower_name.endswith((".toml", ".yaml", ".yml", ".json", ".ini")):
        return "config"
    return "project"


def infer_directory_role(path: str) -> str:
    posix = normalize_path(path)
    name = PurePosixPath(posix).name.lower()
    if name in {"src", "lib", "app", "pkg", "cmd"}:
        return "source"
    if name in {"test", "tests", "__tests__", "spec"}:
        return "tests"
    if name in {"docs", "doc"}:
        return "docs"
    if name in {"examples", "sample", "samples"}:
        return "examples"
    if name in {"scripts", "bin", "tools"}:
        return "scripts"
    if name in {".github", ".gitlab", "ci"}:
        return "ci"
    return "project"


def is_doc(path: str) -> bool:
    posix = normalize_path(path)
    name = PurePosixPath(posix).name
    return name in DOC_NAMES or PurePosixPath(posix).suffix.lower() in {".md", ".rst"}


def is_entry_point(path: str) -> bool:
    posix = normalize_path(path)
    name = PurePosixPath(posix).name
    return posix in ENTRY_NAMES or name in ENTRY_NAMES
