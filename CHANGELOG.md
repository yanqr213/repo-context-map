# Changelog

## 0.4.0 - 2026-06-09

- Added TODO/FIXME-style task marker detection to Markdown, JSON, and agent brief outputs.
- Rebuilt the README with readable English and Chinese usage notes.

## 0.3.0

- Added `--format manifest` to write the recommended AI context pack as a newline-delimited file list.
- Added `--format context-bundle` to emit a paste-ready Markdown bundle with selected file contents.
- Made the context-pack output easier to chain into tools such as `prompt-context-gate`.
- Added tests and CI smoke coverage for manifest and context-bundle outputs.
- Expanded Chinese and English README usage notes for agent context workflows.

## 0.2.0

- Added `--format agent-brief` for paste-ready coding-agent handoff briefs.
- Added agent brief tests and CI smoke coverage.
- Updated project URLs to the public GitHub repository.

## 0.1.0

- Initial release of the offline repository context map CLI.
- Added Markdown and JSON reports, optional Mermaid dependency graph, JSON config, budgeted context pack, and `--check` risk gate.
- Added support for common Python, Node, Go, and Rust manifests.
- Added tests, examples, and GitHub Actions CI.
