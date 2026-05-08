# IMAGEGEN KNOWLEDGE BASE

**Generated:** 2026-04-21
**Commit:** 2cb0bd0
**Branch:** feature/initial-setup

## OVERVIEW

CLI tool wrapping NanoBanana API providers for image generation. Stack: click + google-genai + rich + Pillow, packaged with uv (uv_build backend).

## STRUCTURE

```
imagegen/
├── src/imagegen/        # All source
│   ├── __init__.py      # Package init + dynamic version
│   ├── __main__.py      # python -m imagegen support
│   ├── models.py        # ResolvedModel dataclass
│   ├── cli.py           # Click entrypoint — groups: main, provider
│   ├── provider.py      # Provider config loading + model resolution
│   ├── session.py       # Chat session management (create/load/save/list)
│   ├── chat.py          # Multi-turn chat REPL mode
│   ├── backends/        # Backend implementations
│   │   ├── __init__.py  # Backend dispatch (generate/edit router)
│   │   ├── genai.py     # Google GenAI backend
│   │   └── openai.py    # OpenAI backend
│   └── provider.json.example  # Provider config template
├── docs/                # Documentation
├── references/          # NanoBanana model capability docs (read-only reference)
├── tests/               # Test suite
│   ├── test_prompt_quotes.py
│   ├── test_provider.py
│   ├── test_session.py
│   ├── test_backends_genai.py
│   └── test_backends_openai.py
└── pyproject.toml       # uv_build, entry: imagegen.cli:main
```

## WHERE TO LOOK

| Task | Location | Notes |
|------|----------|-------|
| Add CLI command | `src/imagegen/cli.py` | Click groups: `main` (root), `provider` (subgroup) |
| Add provider/model | `provider.json` | Schema: see `provider.json.example` |
| Change API call logic | `src/imagegen/backends/genai.py` or `src/imagegen/backends/openai.py` | Backend-specific generation |
| Fix model resolution | `src/imagegen/provider.py` | `resolve_model` parses `provider/model` spec → `ResolvedModel` |
| Provider file lookup | `src/imagegen/provider.py` | `_find_provider_file`: CWD → user config → auto-create |
| Session management | `src/imagegen/session.py` | create/load/save/list sessions |
| Chat REPL | `src/imagegen/chat.py` | Multi-turn interactive mode |
| Understand architecture | `docs/development.md` | Full module documentation |

## CODE MAP

| Symbol | Type | Location | Role |
|--------|------|----------|------|
| `main` | click.Group | cli.py | Root CLI group |
| `provider` | click.Group | cli.py | `imagegen provider` subcommand group |
| `provider_list` | command | cli.py | Lists providers/models from provider.json |
| `provider_init` | command | cli.py | Initialize user config |
| `provider_sessions` | command | cli.py | List chat sessions |
| `generate` | command | cli.py | Text-to-image generation |
| `edit` | command | cli.py | Image editing with reference images |
| `chat` | command | cli.py | Multi-turn interactive chat |
| `ResolvedModel` | dataclass | models.py | Result of resolve_model() |
| `load_providers` | function | provider.py | JSON parse of provider.json |
| `resolve_model` | function | provider.py | `"provider/model"` → ResolvedModel |
| `get_model_options` | function | provider.py | Extract model options with defaults |
| `validate_option` | function | provider.py | Validate option value against allowed list |
| `generate` | function | backends/__init__.py | Route generate call to correct backend |
| `edit` | function | backends/__init__.py | Route edit call to correct backend |
| `extract_parts` | function | backends/genai.py | Null-safe response part extraction |
| `extract_and_save_image` | function | backends/genai.py | Extract image from response and save |
| `create_session` | function | session.py | Create new chat session |
| `load_session` | function | session.py | Load existing session metadata |
| `save_turn` | function | session.py | Persist a single chat turn |
| `list_sessions` | function | session.py | List all sessions |
| `run_chat` | function | chat.py | REPL main loop |

## CALL FLOW

```
CLI generate <prompt> <model_spec> <output>
  → resolve_model(model_spec)        # "prov/model" → ResolvedModel
  → _validate_generate_options(...)  # check backend-specific options
  → backends.generate(backend, prompt, base_url, model_name, api_key, output, ...)
    → genai.generate(...) or openai.generate(...)
```

## CONVENTIONS

- `from __future__ import annotations` — every module, no exceptions
- Error handling: `print(msg, file=sys.stderr)` + `sys.exit(1)` — no custom exceptions
- All CLI args are positional — intentional for quick shell invocation
- Type annotations on all functions — Pyright-compatible
- Null-safe response extraction — check each level (candidates, content, parts, inline_data)

## ANTI-PATTERNS (THIS PROJECT)

- **DO NOT** raise exceptions for user-facing errors — use stderr print + sys.exit(1)
- **DO NOT** assume provider.json is in package dir — it uses CWD-first lookup

## KNOWN ISSUES

1. **API key in provider.json** — committed to repo. Should use env vars or secrets manager. (IMAGEGEN_API_KEY env var fallback now supported)
2. **sys.exit in library functions** — `provider.py` calls `sys.exit(1)` directly, making functions untestable in isolation (use `pytest.raises(SystemExit)` in tests).
3. **Chat session resume** — `--session` restores turn index and metadata but does not replay conversation history to the API client.

## COMMANDS

```bash
# Install (dev mode)
uv sync --group dev --group test

# Run CLI
uv run imagegen generate "a cat" "my-provider/gemini-2.5-flash-image" output.png
uv run imagegen provider list
uv run imagegen provider list --model
uv run imagegen provider list --options

# Lint / Type check
uv run ruff check src/
uv run mypy src/

# Test
uv run pytest -v
```

## MUST TO DO

1. 开发请遵循 `docs/development.md` 中的开发规范。
2. 每次完成请求中的代码修改后，进行项目的 git 管理（add、commit 等）。