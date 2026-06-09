# repo-context-map

`repo-context-map` 是一个离线 Python CLI，用来给 Codex、Claude Code、Cursor 等 AI 编程助手生成紧凑、可审查的仓库上下文简报。它只读取本地文件，不上传源码，也不调用在线模型。

它会扫描本地仓库并输出：

- 源码树信号、语言分布、文件角色和目录角色
- 可能的入口文件、关键文档、依赖 manifest
- 测试、lint、format、启动命令候选
- 大文件、复杂文件、Git 近期改动热点和风险文件
- TODO/FIXME/XXX/HACK/BUG/OPTIMIZE 等任务标记，包含文件和行号
- 推荐交给 AI agent 的上下文包、manifest 或可直接粘贴的 context bundle

## 安装

开发安装：

```bash
python -m pip install -e ".[dev]"
```

普通安装：

```bash
python -m pip install .
```

安装后：

```bash
repo-context-map --version
```

未安装时也可以从源码运行：

```bash
PYTHONPATH=src python -m repo_context_map --version
```

## 快速开始

扫描当前仓库并输出 Markdown：

```bash
repo-context-map scan .
```

输出 JSON：

```bash
repo-context-map scan . --format json
```

生成适合直接贴给 Codex、Claude Code、Cursor 的 agent brief：

```bash
repo-context-map scan . --format agent-brief --output AGENT_BRIEF.md
```

只输出推荐上下文路径，一行一个：

```bash
repo-context-map scan . --format manifest --output context-manifest.txt
```

生成包含推荐文件内容的 Markdown context bundle：

```bash
repo-context-map scan . --format context-bundle --budget 3500 --output context-bundle.md
```

写入报告，父目录会自动创建：

```bash
repo-context-map scan . --output reports/context-map.md
```

附带 Mermaid 依赖图：

```bash
repo-context-map scan . --mermaid --output reports/context-map.md
```

CI 或预检模式：

```bash
repo-context-map scan . --check
```

## 配置

示例 `repo-context-map.json`：

```json
{
  "ignore": ["fixtures/", "*.snap"],
  "max_file_size": 400000,
  "budget": 4500,
  "include_gitignore": true,
  "include_mermaid": false
}
```

使用配置运行：

```bash
repo-context-map scan . --config repo-context-map.json
```

## 输出说明

- `Language Distribution`：按语言统计文件数、行数和字节数。
- `Directory Roles`：推断目录用途，例如 source、tests、docs、examples、scripts、CI。
- `Entry Points`：常见入口文件，例如 `main.py`、`cli.py`、`index.ts`、`src/main.rs`。
- `Dependency Summary`：读取 `pyproject.toml`、`requirements.txt`、`package.json`、`go.mod`、`Cargo.toml` 等常见 manifest。
- `Command Candidates`：推断测试、lint、format、启动命令。
- `Documentation Index`：README、CHANGELOG、CONTRIBUTING、docs 文件等。
- `Largest Files` / `Most Complex Files`：提示可能需要谨慎阅读或拆分的文件。
- `Recent Change Hotspots`：有本地 Git 历史时，统计近期频繁改动文件。
- `Task Markers`：从常见注释行提取 TODO/FIXME-style 标记，给 AI agent 快速定位未完成事项。
- `Risk Files`：敏感命名、大文件、高复杂度等风险信号。
- `Recommended AI Context Pack`：在 token 预算内推荐最值得提供给 AI agent 的文件集合。
- `Agent Repository Brief`：`--format agent-brief` 输出的精简交接简报。
- `manifest`：一行一个推荐上下文路径，适合后续脚本或 `prompt-context-gate` 等工具继续处理。
- `context-bundle`：包含推荐文件内容、选择原因和估算 token 的 Markdown 包。

## CI 示例

```yaml
- run: python -m pip install .
- run: repo-context-map scan . --check --output reports/context-map.md
- run: repo-context-map scan . --format manifest --output reports/context-manifest.txt
- run: repo-context-map scan . --format context-bundle --budget 3500 --output reports/context-bundle.md
```

本仓库自带 CI 会在 Python 3.9 到 3.12 上运行测试和 CLI 烟测。

## 示例仓库

`examples/sample-python` 是一个可扫描的小型 Python 仓库：

```bash
repo-context-map scan examples/sample-python --mermaid
repo-context-map scan examples/sample-python --format agent-brief --output AGENT_BRIEF.md
repo-context-map scan examples/sample-python --format manifest --output context-manifest.txt
repo-context-map scan examples/sample-python --format context-bundle --output context-bundle.md
```

## 适用场景

- 给 AI 编程助手派活前生成仓库简报。
- 在代码评审、交接、事故分析前快速摸清仓库结构。
- 在 CI 中检查仓库是否缺少基本测试、文档或命令信号。
- 为多仓库维护者生成一致的上下文包。
- 找出注释里的 TODO/FIXME-style 未完成事项，辅助 agent 切任务。

## 限制

- `.gitignore` 支持是轻量实现，不是完整 Git ignore 引擎。
- 复杂度是基于分支关键字的启发式估算，不替代语言专用静态分析。
- 依赖摘要覆盖常见 manifest，不解析所有 lockfile 细节。
- Git 热点依赖本地 Git 历史；没有 `.git` 时会跳过。
- 任务标记检测只匹配常见注释前缀，不是 issue tracker，也不是 AST 级语义解析。
- 默认离线运行，不上传源码，不调用在线模型。

## English

`repo-context-map` is an offline Python CLI for building compact repository briefings for AI coding agents such as Codex, Claude Code, Cursor, and similar tools. It scans a local repository and reports source tree signals, languages, file roles, directory roles, entry points, dependency manifests, command candidates, documentation, recent Git hotspots, risk files, TODO/FIXME-style task markers, and recommended context packs.

### Install

```bash
python -m pip install -e ".[dev]"
python -m pip install .
```

### Usage

```bash
repo-context-map scan .
repo-context-map scan . --format json
repo-context-map scan . --format agent-brief --output AGENT_BRIEF.md
repo-context-map scan . --format manifest --output context-manifest.txt
repo-context-map scan . --format context-bundle --budget 3500 --output context-bundle.md
repo-context-map scan . --check
```

The `agent-brief` format is designed to be pasted into AI coding agents before assigning work. The `manifest` format writes one recommended context path per line for downstream tooling. The `context-bundle` format writes selected file contents into Markdown for small repositories or focused tasks.

### Privacy And Limits

The tool reads local files only and does not upload code or call online models. Task marker detection is intentionally lightweight: it extracts common TODO/FIXME-style comments with file and line references, but it is not a full issue tracker or language AST analyzer.
