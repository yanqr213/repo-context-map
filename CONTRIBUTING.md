# Contributing

Thanks for helping improve `repo-context-map`.

## Development

```bash
python -m pip install -e ".[dev]"
python -m pytest
repo-context-map scan . --output reports/context-map.md
```

## Guidelines

- Keep the default scanner offline and standard-library first.
- Prefer small, explainable heuristics over opaque behavior.
- Add tests for new detection rules and CLI behavior.
- Do not add real credentials, personal emails, production tokens, or private repository URLs.
- Use `.test` domains in examples and documentation.

## Release Checklist

- Run `python -m pytest`.
- Run a CLI smoke test against `examples/sample-python`.
- Update `CHANGELOG.md` for user-visible changes.
- Verify README examples still work.
