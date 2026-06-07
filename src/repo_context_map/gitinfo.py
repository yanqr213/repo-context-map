from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Dict, List


def collect_hotspots(root: Path, limit: int = 10) -> List[Dict[str, object]]:
    if not (root / ".git").exists():
        return []
    try:
        output = subprocess.check_output(
            ["git", "-C", str(root), "log", "--name-only", "--pretty=format:", "--since=90 days"],
            text=True,
            stderr=subprocess.DEVNULL,
            timeout=5,
        )
    except (OSError, subprocess.SubprocessError):
        return []
    counts: Dict[str, int] = {}
    for line in output.splitlines():
        path = line.strip()
        if path:
            counts[path] = counts.get(path, 0) + 1
    return [{"path": path, "changes": count} for path, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))[:limit]]
