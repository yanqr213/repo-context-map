from __future__ import annotations

import argparse
import sys
from typing import List, Optional

from . import __version__
from .config import build_scan_config
from .report import to_agent_brief, to_context_bundle, to_json, to_manifest, to_markdown, write_report
from .scanner import scan_repository


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "scan":
        return _scan(args)
    parser.print_help()
    return 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="repo-context-map", description="Build repository context maps for AI coding agents.")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    subparsers = parser.add_subparsers(dest="command")
    scan = subparsers.add_parser("scan", help="Scan a local repository.")
    scan.add_argument("path", nargs="?", default=".", help="Repository path to scan.")
    scan.add_argument(
        "--format",
        choices=["markdown", "json", "agent-brief", "manifest", "context-bundle"],
        default="markdown",
        help="Output format.",
    )
    scan.add_argument("--output", "-o", default="", help="Write report to this path. Parent directories are created.")
    scan.add_argument("--config", default="", help="Optional JSON config path.")
    scan.add_argument("--budget", type=int, default=5000, help="Approximate token budget for the recommended context pack.")
    scan.add_argument("--max-file-size", type=int, default=512_000, help="Skip files larger than this many bytes.")
    scan.add_argument("--mermaid", action="store_true", help="Include a Mermaid dependency graph in Markdown or JSON.")
    scan.add_argument("--check", action="store_true", help="Return non-zero when repository risks are detected.")
    return parser


def _scan(args: argparse.Namespace) -> int:
    config = build_scan_config(
        root=args.path,
        config_path=args.config,
        max_file_size=args.max_file_size,
        budget=args.budget,
        include_mermaid=args.mermaid,
        check=args.check,
    )
    repo_map = scan_repository(config)
    if args.format == "json":
        content = to_json(repo_map)
    elif args.format == "agent-brief":
        content = to_agent_brief(repo_map)
    elif args.format == "manifest":
        content = to_manifest(repo_map)
    elif args.format == "context-bundle":
        content = to_context_bundle(repo_map)
    else:
        content = to_markdown(repo_map)
    if args.output:
        write_report(content, args.output)
    else:
        sys.stdout.write(content)
    if args.check and repo_map.risks:
        for risk in repo_map.risks:
            print(f"check: {risk}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
