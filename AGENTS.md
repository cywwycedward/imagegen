# IMAGEGEN KNOWLEDGE BASE

**Generated:** 2026-04-21
**Commit:** 2cb0bd0
**Branch:** feature/initial-setup

## OVERVIEW

CLI tool wrapping NanoBanana API providers for image generation. Stack: click + google-genai + rich + Pillow, packaged with uv (uv_build backend).

## STRUCTURE

```
imagegen/
├── src/imagegen/        # All source (5 files, ~190 lines total)
│   ├── cli.py           # Click entrypoint — two groups: `provider`, `generate`
│   ├── provider.py      # Provider config loading + model resolution
│   └── generate.py      # genai.Client call + image extraction + save
├── provider.json        # Provider/model registry (⚠ contains API key)
├── docs/development.md  # Authoritative dev guide (544 lines) — READ FIRST
├── references/          # NanoBanana model capability docs (read-only reference)
├── tests/               # Empty — no tests written yet
└── pyproject.toml       # uv_build, entry: imagegen.cli:main
```

## WHERE TO LOOK

| Task | Location | Notes |
|------|----------|-------|
| Add CLI command | `src/imagegen/cli.py` | Click groups: `main` (root), `provider` (subgroup) |
| Add provider/model | `provider.json` | Schema: `{provider: {base_url, api_key, models: {key: name}}}` |
| Change API call logic | `src/imagegen/generate.py` | Single function `generate_image` |
| Fix model resolution | `src/imagegen/provider.py` | `resolve_model` parses `provider:model` spec |
| Provider file lookup | `src/imagegen/provider.py` | `_find_provider_file`: CWD → importlib.resources fallback |
| Understand architecture | `docs/development.md` | Sections 1-7 cover everything |

## CODE MAP

| Symbol | Type | Location | Role |
|--------|------|----------|------|
| `main` | click.Group | cli.py:14 | Root CLI group |
| `provider` | click.Group | cli.py:19 | `imagegen provider` subcommand group |
| `provider_list` | command | cli.py:24 | Lists providers/models from provider.json |
| `generate` | command | cli.py:52 | Main command: prompt → API → image file |
| `generate_image` | function | generate.py:13 | genai.Client call, response parsing, file write |
| `load_providers` | function | provider.py:36 | JSON parse of provider.json |
| `resolve_model` | function | provider.py:52 | `"provider:model"` → (base_url, model_name, model_key) |
| `_find_provider_file` | function | provider.py:14 | Two-level config file discovery |
| `PROVIDER_FILENAME` | const | provider.py:12 | `"provider.json"` |

## CALL FLOW

```
CLI generate <prompt> <model_spec> <api_key> <output>
  → resolve_model(model_spec)        # "nanobnn:flux" → (url, name, key)
  → generate_image(prompt, url, name, key, path)
    → genai.Client(api_key, http_options={base_url})
    → client.models.generate_content(model, prompt, config={response_modalities:["IMAGE"]})
    → response.candidates[0].content.parts[0].inline_data  # null-safe chain
    → pathlib.Path(path).write_bytes(data)
```

## CONVENTIONS

- `from __future__ import annotations` — every module, no exceptions
- Error handling: `print(msg, file=sys.stderr)` + `sys.exit(1)` — no custom exceptions
- All CLI args are positional — intentional for quick shell invocation
- Type annotations on all functions — Pyright-compatible
- Null-safe response extraction — check each level (candidates, content, parts, inline_data)

## ANTI-PATTERNS (THIS PROJECT)

- **DO NOT** raise exceptions for user-facing errors — use stderr print + sys.exit(1)
- **DO NOT** add optional CLI flags where positional args exist — project uses positional-only design
- **DO NOT** assume provider.json is in package dir — it uses CWD-first lookup

## KNOWN ISSUES

1. **provider.json at repo root** — importlib.resources fallback looks in `src/imagegen/` package, but file lives at project root. Fallback broken when installed as wheel.
2. **API key in provider.json** — committed to repo. Should use env vars or secrets manager.
3. **No tests** — `tests/` exists with empty `__init__.py`. pytest configured but no test files.
4. **sys.exit in library functions** — `provider.py` calls `sys.exit(1)` directly, making functions untestable in isolation.
5. **No CI/CD** — no GitHub Actions, Makefile, or pre-commit hooks.

## COMMANDS

```bash
# Install (dev mode)
uv sync

# Run CLI
uv run imagegen generate "a cat" "nanobnn:flux-1-schnell" "YOUR_KEY" output.png
uv run imagegen provider list
uv run imagegen provider list --model

# Lint / Type check (configured but no custom rules)
uv run ruff check src/
uv run mypy src/

# Test (empty suite)
uv run pytest
```

## MUST TO DO

1. 开发请遵循 `docs/development.md` 中的开发规范。
2. 每次完成请求中的代码修改后，进行项目的 git 管理（add、commit 等）。