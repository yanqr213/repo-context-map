from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from .models import ScanConfig


def load_config(path: str, root: Path) -> Dict[str, Any]:
    if not path:
        return {}
    config_path = Path(path)
    if not config_path.is_absolute():
        config_path = root / config_path
    data = json.loads(config_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Config JSON must contain an object.")
    return data


def build_scan_config(
    root: str,
    config_path: str = "",
    max_file_size: int = 512_000,
    budget: int = 5000,
    include_mermaid: bool = False,
    check: bool = False,
) -> ScanConfig:
    root_path = Path(root).resolve()
    loaded = load_config(config_path, root_path)
    ignore_patterns: List[str] = list(loaded.get("ignore", []))
    return ScanConfig(
        root=root_path,
        max_file_size=int(loaded.get("max_file_size", max_file_size)),
        ignore_patterns=ignore_patterns,
        include_gitignore=bool(loaded.get("include_gitignore", True)),
        include_mermaid=bool(loaded.get("include_mermaid", include_mermaid)),
        budget=int(loaded.get("budget", budget)),
        check=check,
    )
