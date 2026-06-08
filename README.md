# repo-context-map

`repo-context-map` 是一个离线 CLI，用来给 AI coding agents 生成高质量仓库 briefing。它会扫描本地仓库，输出源码树线索、语言和文件类型分布、入口点、依赖摘要、测试/格式化/启动命令候选、关键文档、近期改动热点、风险文件，以及适合直接贴给 Codex、Claude Code、Cursor 的推荐上下文包。

它适合在派活前快速回答这些问题：

- 这个仓库主要是什么语言和结构？
- 哪些文件最值得先给 AI 读？
- 测试、格式化、启动命令可能是什么？
- 最近频繁改动或风险较高的文件在哪里？
- 缺测试、缺文档、可疑敏感文件等风险是否应该先处理？

## 安装

开发安装：

```bash
python -m pip install -e ".[dev]"
```

普通安装：

```bash
python -m pip install .
```

安装后可使用：

```bash
repo-context-map --version
```

未安装时也可以从源码运行：

```bash
PYTHONPATH=src python -m repo_context_map --version
```

## 快速使用

扫描当前仓库并输出 Markdown：

```bash
repo-context-map scan .
```

输出 JSON：

```bash
repo-context-map scan . --format json
```

生成可直接贴给 Codex、Claude Code、Cursor 的 agent brief：

```bash
repo-context-map scan . --format agent-brief --output AGENT_BRIEF.md
```

写入文件，父目录会自动创建：

```bash
repo-context-map scan . --output reports/context-map.md
```

附带 Mermaid 依赖图：

```bash
repo-context-map scan . --mermaid --output reports/context-map.md
```

限制推荐上下文包预算：

```bash
repo-context-map scan . --budget 3000
```

CI 或预检模式：检测到缺少测试、文档、测试命令或风险文件时返回非零。

```bash
repo-context-map scan . --check
```

## 配置 JSON

示例：

```json
{
  "ignore": ["fixtures/", "*.snap"],
  "max_file_size": 400000,
  "budget": 4500,
  "include_gitignore": true,
  "include_mermaid": false
}
```

运行：

```bash
repo-context-map scan . --config repo-context-map.json
```

## 输出解释

- `Language Distribution`：按语言统计文件数、行数和字节数。
- `Directory Roles`：推断目录角色，例如 source、tests、docs、examples、scripts、ci。
- `Entry Points`：常见入口文件，例如 `main.py`、`cli.py`、`index.ts`、`src/main.rs`。
- `Dependency Summary`：读取 `pyproject.toml`、`requirements.txt`、`package.json`、`go.mod`、`Cargo.toml`。
- `Command Candidates`：推断测试、格式化、lint、启动命令。
- `Documentation Index`：列出 README、CHANGELOG、CONTRIBUTING、docs 下的文档等。
- `Largest Files` / `Most Complex Files`：用大小和分支关键字估算需要谨慎阅读的文件。
- `Recent Change Hotspots`：当仓库有 Git 历史时，统计最近 90 天频繁改动的文件。
- `Risk Files`：提示可能包含敏感信息、过大或复杂度过高的文件。
- `Recommended AI Context Pack`：在预算内推荐最值得提供给 AI agent 的文件集合。
- `Agent Repository Brief`：`--format agent-brief` 输出的精简交接简报，按先读文件、可尝试命令、依赖 manifest、推荐上下文包、风险和建议工作流组织。

## CI 用法

GitHub Actions 中可直接安装并运行：

```yaml
- run: python -m pip install .
- run: repo-context-map scan . --check --output reports/context-map.md
```

本仓库自带 CI 会在 Python 3.9 到 3.12 上运行测试和 CLI 烟测。

## 示例

`examples/sample-python` 是一个可扫描的小型 Python 仓库：

```bash
repo-context-map scan examples/sample-python --mermaid
repo-context-map scan examples/sample-python --format agent-brief --output AGENT_BRIEF.md
```

## 适用场景

- 给 AI 编程代理派活前生成仓库简报。
- 在代码评审、交接、事故分析前快速摸清仓库结构。
- 在 CI 中检查仓库是否缺少基本测试或文档。
- 为多仓库维护者生成一致的上下文包。

## 限制

- `.gitignore` 支持基础通配和目录忽略，不是完整 Git ignore 引擎。
- 复杂度是轻量启发式估算，不替代语言专用分析器。
- 依赖摘要只覆盖常见 manifest，并不会解析所有 lockfile 细节。
- 热点统计依赖本地 Git 历史；没有 `.git` 时会跳过。
- 默认离线运行，不会上传源码，也不会调用在线模型。

## English Summary

`repo-context-map` is an offline Python CLI that builds repository context maps for AI coding agents. It scans a local codebase and emits Markdown, JSON, or paste-ready agent brief reports with language distribution, directory roles, entry points, dependency manifests, command candidates, documentation index, large or complex files, Git change hotspots, risk signals, and a recommended context pack.

Typical use:

```bash
repo-context-map scan . --output reports/context-map.md
repo-context-map scan . --format json
repo-context-map scan . --format agent-brief --output AGENT_BRIEF.md
repo-context-map scan . --check
```

The `agent-brief` format is designed to be pasted into Codex, Claude Code, Cursor, or similar coding agents before assigning work. It highlights start files, likely commands, dependency manifests, risk files, and a suggested workflow.
