# Contributing to imagegen

Thanks for your interest in contributing! Here's how to get started.

## Development Setup

```bash
# Clone the repo
git clone https://github.com/cywwycedward/imagegen.git
cd imagegen

# Install with dev dependencies
uv sync --group dev --group test

# Verify setup
uv run imagegen --help
```

## Development Workflow

1. Create a feature branch from `develop`:
   ```bash
   git checkout develop
   git checkout -b feature/your-feature
   ```

2. Make changes following the conventions in `docs/development.md`.

3. Run checks before committing:
   ```bash
   uv run ruff check src/
   uv run ruff format src/
   uv run mypy src/
   uv run pytest
   ```

4. Commit with [conventional commits](https://www.conventionalcommits.org/):
   ```
   feat: add new provider support
   fix: correct model resolution for edge case
   docs: update usage examples
   ```

5. Open a PR targeting the `develop` branch.

## Code Conventions

- `from __future__ import annotations` in every module
- Type annotations on all functions (Pyright-compatible)
- Error handling: `print(msg, file=sys.stderr)` + `sys.exit(1)` — no custom exceptions
- Positional CLI arguments only — no optional flags for core args

## Branch Strategy

- `main` — stable releases only
- `develop` — integration branch
- `feature/*` — new features
- `release/*` — release preparation

## Pre-commit Hooks (Optional)

```bash
pip install pre-commit
pre-commit install
```

This will run ruff and mypy checks automatically on each commit.
