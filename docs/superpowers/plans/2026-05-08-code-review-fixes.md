# Code Review Fixes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix all issues identified in the code review: 2 Critical bugs, 5 Important improvements, and 4 Nice-to-have enhancements.

**Architecture:** Introduce a `ResolvedModel` dataclass and a `BackendProtocol` registry to replace the raw tuple and if/elif dispatch. Extract shared image-extraction logic into a helper. Add comprehensive tests for `provider.py`, `session.py`, and backends. Fix file handle leaks and OpenAI multi-image generation. Support env var API keys and dynamic version via `importlib.metadata`.

**Tech Stack:** Python 3.10+, click, google-genai, openai, rich, Pillow, pytest, uv

**Branch:** `feature/code-review-fixes` (from `develop`)

---

## File Map

| Action | File | Responsibility |
|--------|------|---------------|
| Modify | `src/imagegen/backends/openai.py` | Fix mask handle leak; use `n` param for multi-image |
| Create | `src/imagegen/models.py` | `ResolvedModel` dataclass |
| Modify | `src/imagegen/provider.py` | Return `ResolvedModel`; env var API key support |
| Modify | `src/imagegen/backends/__init__.py` | Backend registry; adapt to `ResolvedModel` |
| Modify | `src/imagegen/backends/genai.py` | Extract `extract_image_from_response()` as public |
| Modify | `src/imagegen/chat.py` | Use shared `extract_image_from_response()` |
| Modify | `src/imagegen/cli.py` | Adapt to `ResolvedModel` attribute access |
| Modify | `src/imagegen/__init__.py` | Dynamic version via `importlib.metadata` |
| Modify | `.gitignore` | Add `.imagegen/` |
| Modify | `AGENTS.md` | Sync code map with current codebase |
| Modify | `docs/development.md` | Sync directory structure and module descriptions |
| Create | `tests/test_provider.py` | Tests for resolve_model, validate_option, load_providers |
| Create | `tests/test_session.py` | Tests for create/load/save/list sessions |
| Create | `tests/test_backends_genai.py` | Tests for config building and image extraction |
| Create | `tests/test_backends_openai.py` | Tests for client building, file handling, multi-image |

---

### Task 1: Fix Critical — OpenAI mask file handle leak & multi-image API efficiency

**Files:**
- Modify: `src/imagegen/backends/openai.py`

- [ ] **Step 1: Fix mask file handle leak in `edit()`**

In `src/imagegen/backends/openai.py`, the mask file opened at line 126 is never closed. Refactor the `edit()` function to track all file handles and close them in `finally`:

```python
def edit(
    prompt: str,
    images: list[Path],
    base_url: str,
    model_name: str,
    api_key: str,
    output: Path,
    size: str | None = None,
    quality: str | None = None,
    background: str | None = None,
    output_format: str | None = None,
    output_compression: int | None = None,
    n: int | None = None,
    mask: str | None = None,
    input_fidelity: str | None = None,
) -> None:
    client = _build_client(api_key, base_url)

    if not images:
        print("Error: at least one image is required for editing.", file=sys.stderr)
        sys.exit(1)

    open_files: list[BufferedReader] = []
    try:
        image_files: list[BufferedReader] = [open(img, "rb") for img in images]  # noqa: SIM115
        open_files.extend(image_files)

        kwargs: dict[str, Any] = {
            "model": model_name,
            "prompt": prompt,
            "image": image_files if len(image_files) > 1 else image_files[0],
            "response_format": "b64_json",
        }
        if size is not None:
            kwargs["size"] = size
        if quality is not None:
            kwargs["quality"] = quality
        if background is not None:
            kwargs["background"] = background
        if output_format is not None:
            kwargs["output_format"] = output_format
        if output_compression is not None:
            kwargs["output_compression"] = output_compression
        if mask is not None:
            mask_file = open(mask, "rb")  # noqa: SIM115
            open_files.append(mask_file)
            kwargs["mask"] = mask_file
        if input_fidelity is not None:
            kwargs["input_fidelity"] = input_fidelity

        num_images = n if n is not None else 1

        for i in range(num_images):
            response = client.images.edit(**kwargs)
            image_data = response.data[0] if response.data else None
            if image_data is None:
                print("Error: empty response from API.", file=sys.stderr)
                sys.exit(1)

            if num_images == 1:
                target = output
            else:
                target = output.parent / f"{output.stem}_{i}{output.suffix}"

            _save_image(image_data.b64_json, target)
    finally:
        for f in open_files:
            f.close()
```

- [ ] **Step 2: Fix multi-image generate to use `n` parameter instead of loop**

In the same file, replace the loop in `generate()` with a single API call using the `n` kwarg:

```python
def generate(
    prompt: str,
    base_url: str,
    model_name: str,
    api_key: str,
    output: Path,
    size: str | None = None,
    quality: str | None = None,
    background: str | None = None,
    output_format: str | None = None,
    output_compression: int | None = None,
    n: int | None = None,
    style: str | None = None,
) -> None:
    client = _build_client(api_key, base_url)

    kwargs: dict[str, Any] = {
        "model": model_name,
        "prompt": prompt,
        "response_format": "b64_json",
    }
    if size is not None:
        kwargs["size"] = size
    if quality is not None:
        kwargs["quality"] = quality
    if background is not None:
        kwargs["background"] = background
    if output_format is not None:
        kwargs["output_format"] = output_format
    if output_compression is not None:
        kwargs["output_compression"] = output_compression
    if style is not None:
        kwargs["style"] = style
    if n is not None:
        kwargs["n"] = n

    response = client.images.generate(**kwargs)

    if not response.data:
        print("Error: empty response from API.", file=sys.stderr)
        sys.exit(1)

    for i, image_data in enumerate(response.data):
        if len(response.data) == 1:
            target = output
        else:
            target = output.parent / f"{output.stem}_{i}{output.suffix}"
        _save_image(image_data.b64_json, target)
```

- [ ] **Step 3: Run lint and type checks**

Run: `uv run ruff check src/imagegen/backends/openai.py && uv run mypy src/imagegen/backends/openai.py`
Expected: All checks passed

- [ ] **Step 4: Commit**

```bash
git add src/imagegen/backends/openai.py
git commit -m "fix(backends): close mask file handle and use n param for multi-image generation

- Track all opened file handles in a single list and close in finally block
- Replace per-image API loop with single call using n parameter
- Iterate response.data to save multiple images"
```

---

### Task 2: Introduce `ResolvedModel` dataclass

**Files:**
- Create: `src/imagegen/models.py`
- Modify: `src/imagegen/provider.py`
- Modify: `src/imagegen/cli.py`
- Modify: `src/imagegen/chat.py` (indirect via cli.py — chat receives individual args)

- [ ] **Step 1: Create `models.py` with `ResolvedModel` dataclass**

Create `src/imagegen/models.py`:

```python
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ResolvedModel:
    """Result of resolving a 'provider/model' spec against provider.json."""

    backend: str
    base_url: str
    model_name: str
    display_name: str
    api_key: str
    options: dict[str, list[str]]
```

- [ ] **Step 2: Update `provider.py` to return `ResolvedModel`**

In `src/imagegen/provider.py`, add the import and change `resolve_model` return type:

Add at top of imports:
```python
from imagegen.models import ResolvedModel
```

Replace the return statement in `resolve_model()`:

Old:
```python
def resolve_model(
    provider_model: str,
) -> tuple[str, str, str, str, str, dict[str, list[str]]]:
```
```python
    return (
        backend,
        provider["baseUrl"],
        model_key,
        model_info["name"],
        provider["apiKey"],
        options,
    )
```

New:
```python
def resolve_model(
    provider_model: str,
) -> ResolvedModel:
```
```python
    api_key = provider.get("apiKey", "")
    if not api_key:
        import os

        env_key = os.environ.get("IMAGEGEN_API_KEY", "")
        if env_key:
            api_key = env_key

    return ResolvedModel(
        backend=backend,
        base_url=provider["baseUrl"],
        model_name=model_key,
        display_name=model_info["name"],
        api_key=api_key,
        options=options,
    )
```

This also adds env var fallback for API key (Nice-to-have item 9).

- [ ] **Step 3: Update `cli.py` to use `ResolvedModel` attribute access**

In `src/imagegen/cli.py`, add import:
```python
from imagegen.models import ResolvedModel
```

Replace all tuple unpacking of `resolve_model()` with attribute access. There are 3 call sites:

**`generate` command (around line 215):**

Old:
```python
    backend, base_url, model_name, _display_name, api_key, options = resolve_model(
        model_spec
    )
    _validate_generate_options(
        model_name,
        backend,
        options,
        ...
    )

    backend_generate(
        backend=backend,
        prompt=prompt,
        base_url=base_url,
        model_name=model_name,
        api_key=api_key,
        output=Path(output),
        ...
    )
```

New:
```python
    model = resolve_model(model_spec)
    _validate_generate_options(
        model.model_name,
        model.backend,
        model.options,
        ...
    )

    backend_generate(
        backend=model.backend,
        prompt=prompt,
        base_url=model.base_url,
        model_name=model.model_name,
        api_key=model.api_key,
        output=Path(output),
        ...
    )
```

**`edit` command (around line 334):**

Old:
```python
    backend, base_url, model_name, _display_name, api_key, options = resolve_model(
        model_spec
    )
```

New:
```python
    model = resolve_model(model_spec)
```

Then replace all `backend` → `model.backend`, `base_url` → `model.base_url`, etc.

**`chat` command (around line 406):**

Old:
```python
    backend, base_url, model_name, _display_name, api_key, options = resolve_model(
        model_spec
    )

    if backend != "genai":
        ...

    _validate_generate_options(
        model_name,
        backend,
        options,
        ...
    )

    run_chat(
        base_url=base_url,
        model_name=model_name,
        api_key=api_key,
        ...
    )
```

New:
```python
    model = resolve_model(model_spec)

    if model.backend != "genai":
        ...

    _validate_generate_options(
        model.model_name,
        model.backend,
        model.options,
        ...
    )

    run_chat(
        base_url=model.base_url,
        model_name=model.model_name,
        api_key=model.api_key,
        ...
    )
```

- [ ] **Step 4: Update test fixture**

In `tests/test_prompt_quotes.py`, update `FAKE_RESOLVE` to return a `ResolvedModel`:

```python
from imagegen.models import ResolvedModel

FAKE_RESOLVE = ResolvedModel(
    backend="genai",
    base_url="https://fake.api",
    model_name="fake-model",
    display_name="Fake Model",
    api_key="fake-key",
    options={
        "aspect_ratio": [],
        "image_size": [],
        "grounding": [],
        "size": [],
        "quality": [],
        "background": [],
        "style": [],
    },
)
```

- [ ] **Step 5: Run all checks**

Run: `uv run ruff check src/ && uv run mypy src/ && uv run pytest -v`
Expected: All passed

- [ ] **Step 6: Commit**

```bash
git add src/imagegen/models.py src/imagegen/provider.py src/imagegen/cli.py tests/test_prompt_quotes.py
git commit -m "refactor(provider): replace raw tuple with ResolvedModel dataclass

- Introduce frozen ResolvedModel dataclass in models.py
- resolve_model() now returns ResolvedModel instead of 6-tuple
- Add IMAGEGEN_API_KEY env var fallback when apiKey is empty
- Update cli.py and tests to use attribute access"
```

---

### Task 3: Extract shared image extraction helper from genai backend

**Files:**
- Modify: `src/imagegen/backends/genai.py`
- Modify: `src/imagegen/chat.py`

- [ ] **Step 1: Make `extract_image_from_response` a public reusable function**

In `src/imagegen/backends/genai.py`, rename `_extract_image` to `extract_image` and add a variant that returns bytes instead of writing to file. Also add a helper function for extracting parts from a response:

Replace the `_extract_image` function with two functions:

```python
def extract_parts(
    response: types.GenerateContentResponse,
) -> list[types.Part] | None:
    """Extract parts from a genai response with null-safe traversal."""
    candidate = response.candidates[0] if response.candidates else None
    content = candidate.content if candidate else None
    return content.parts if content else None


def extract_and_save_image(response: types.GenerateContentResponse, output: Path) -> None:
    """Extract first image from response and save to output path."""
    parts = extract_parts(response)

    if not parts:
        print("Error: empty response from API.", file=sys.stderr)
        sys.exit(1)

    for part in parts:
        if part.inline_data is not None:
            image_bytes = part.inline_data.data
            if image_bytes is None:
                continue
            if isinstance(image_bytes, str):
                image_bytes = base64.b64decode(image_bytes)
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_bytes(image_bytes)
            print(f"Image saved to {output}")
            return

    text_parts = [p.text for p in parts if p.text]
    if text_parts:
        print("\n".join(text_parts), file=sys.stderr)
    else:
        print("Error: no image in response.", file=sys.stderr)
    sys.exit(1)
```

Update `generate()` and `edit()` in the same file to call `extract_and_save_image` instead of `_extract_image`:

```python
    extract_and_save_image(response, output)
```

- [ ] **Step 2: Update `chat.py` to use the shared extraction logic**

In `src/imagegen/chat.py`, replace the inline image extraction (lines 155-173) with the shared helper.

Add import:
```python
from imagegen.backends.genai import extract_parts
```

Remove existing import of `base64` (no longer needed in chat.py).

Replace the response handling block (from `candidate = response.candidates[0]...` through `console.print(f"[green]Image saved: {image_path}[/green]")`) with:

```python
        parts = extract_parts(response)

        if not parts:
            console.print("[yellow]Empty response.[/yellow]")
            continue

        image_path: Path | None = None
        for part in parts:
            if part.text:
                console.print(part.text)
            if part.inline_data is not None and part.inline_data.data is not None:
                image_bytes = part.inline_data.data
                if isinstance(image_bytes, str):
                    import base64

                    image_bytes = base64.b64decode(image_bytes)
                image_path = output_dir / f"turn_{turn_index:03d}.png"
                image_path.write_bytes(image_bytes)
                console.print(f"[green]Image saved: {image_path}[/green]")
```

Note: We keep the base64 decode inline in chat.py because chat needs to handle each part differently (print text parts, save image parts) rather than using the all-or-nothing `extract_and_save_image()`. The shared `extract_parts()` eliminates the null-safe traversal duplication.

- [ ] **Step 3: Run checks**

Run: `uv run ruff check src/ && uv run mypy src/ && uv run pytest -v`
Expected: All passed

- [ ] **Step 4: Commit**

```bash
git add src/imagegen/backends/genai.py src/imagegen/chat.py
git commit -m "refactor(backends): extract shared response parsing into extract_parts()

- Add public extract_parts() for null-safe response traversal
- Rename _extract_image to extract_and_save_image for clarity
- chat.py now uses extract_parts() instead of duplicating traversal logic"
```

---

### Task 4: Dynamic version via `importlib.metadata`

**Files:**
- Modify: `src/imagegen/__init__.py`

- [ ] **Step 1: Replace hardcoded version with `importlib.metadata`**

Replace the contents of `src/imagegen/__init__.py`:

```python
"""imagegen — CLI tool for generating images using NanoBanana API providers."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("imagegen")
except PackageNotFoundError:
    __version__ = "0.1.0"
```

- [ ] **Step 2: Run checks**

Run: `uv run ruff check src/imagegen/__init__.py && uv run mypy src/imagegen/__init__.py`
Expected: All passed

- [ ] **Step 3: Commit**

```bash
git add src/imagegen/__init__.py
git commit -m "refactor: use importlib.metadata for dynamic version

Falls back to hardcoded '0.1.0' when package metadata is unavailable."
```

---

### Task 5: Update `.gitignore`

**Files:**
- Modify: `.gitignore`

- [ ] **Step 1: Add `.imagegen/` directory to `.gitignore`**

Add the following line to the `# Project-specific` section of `.gitignore`:

```
.imagegen/
```

The full section should read:

```
# Project-specific
.outputs/
provider.json
.imagegen/
```

- [ ] **Step 2: Commit**

```bash
git add .gitignore
git commit -m "chore: add .imagegen/ to gitignore

Prevents project-level provider configs (which contain API keys)
from being committed."
```

---

### Task 6: Add tests for `provider.py`

**Files:**
- Create: `tests/test_provider.py`

- [ ] **Step 1: Write tests for `resolve_model`**

Create `tests/test_provider.py`:

```python
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

from imagegen.models import ResolvedModel
from imagegen.provider import (
    get_model_options,
    load_providers,
    resolve_model,
    validate_backend_option,
    validate_option,
)


def _write_provider_json(tmp_path: Path, providers: list[dict[str, Any]]) -> Path:
    """Write a provider.json under tmp_path/.imagegen/ and return the file path."""
    config_dir = tmp_path / ".imagegen"
    config_dir.mkdir()
    config_file = config_dir / "provider.json"
    config_file.write_text(json.dumps({"providers": providers}))
    return config_file


SAMPLE_PROVIDER: dict[str, Any] = {
    "name": "test-prov",
    "backend": "genai",
    "baseUrl": "https://api.test.com",
    "apiKey": "test-key-123",
    "models": {
        "test-model": {
            "name": "Test Model Display",
            "options": {
                "aspect_ratio": ["1:1", "16:9"],
                "image_size": ["1K", "2K"],
                "grounding": ["google-search"],
            },
        }
    },
}


class TestResolveModel:
    def test_valid_spec(self, tmp_path: Path) -> None:
        _write_provider_json(tmp_path, [SAMPLE_PROVIDER])
        with patch("imagegen.provider.Path.cwd", return_value=tmp_path):
            result = resolve_model("test-prov/test-model")

        assert isinstance(result, ResolvedModel)
        assert result.backend == "genai"
        assert result.base_url == "https://api.test.com"
        assert result.model_name == "test-model"
        assert result.display_name == "Test Model Display"
        assert result.api_key == "test-key-123"
        assert result.options["aspect_ratio"] == ["1:1", "16:9"]

    def test_invalid_format_no_slash(self, tmp_path: Path) -> None:
        _write_provider_json(tmp_path, [SAMPLE_PROVIDER])
        with patch("imagegen.provider.Path.cwd", return_value=tmp_path):
            with pytest.raises(SystemExit):
                resolve_model("no-slash-here")

    def test_unknown_provider(self, tmp_path: Path) -> None:
        _write_provider_json(tmp_path, [SAMPLE_PROVIDER])
        with patch("imagegen.provider.Path.cwd", return_value=tmp_path):
            with pytest.raises(SystemExit):
                resolve_model("unknown-prov/test-model")

    def test_unknown_model(self, tmp_path: Path) -> None:
        _write_provider_json(tmp_path, [SAMPLE_PROVIDER])
        with patch("imagegen.provider.Path.cwd", return_value=tmp_path):
            with pytest.raises(SystemExit):
                resolve_model("test-prov/nonexistent-model")

    def test_env_var_api_key_fallback(self, tmp_path: Path) -> None:
        provider = {**SAMPLE_PROVIDER, "apiKey": ""}
        _write_provider_json(tmp_path, [provider])
        with (
            patch("imagegen.provider.Path.cwd", return_value=tmp_path),
            patch.dict(os.environ, {"IMAGEGEN_API_KEY": "env-key-456"}),
        ):
            result = resolve_model("test-prov/test-model")
        assert result.api_key == "env-key-456"

    def test_env_var_not_used_when_config_has_key(self, tmp_path: Path) -> None:
        _write_provider_json(tmp_path, [SAMPLE_PROVIDER])
        with (
            patch("imagegen.provider.Path.cwd", return_value=tmp_path),
            patch.dict(os.environ, {"IMAGEGEN_API_KEY": "env-key-456"}),
        ):
            result = resolve_model("test-prov/test-model")
        assert result.api_key == "test-key-123"

    def test_default_backend_is_genai(self, tmp_path: Path) -> None:
        provider_no_backend: dict[str, Any] = {
            "name": "prov",
            "baseUrl": "https://example.com",
            "apiKey": "k",
            "models": {"m": {"name": "M"}},
        }
        _write_provider_json(tmp_path, [provider_no_backend])
        with patch("imagegen.provider.Path.cwd", return_value=tmp_path):
            result = resolve_model("prov/m")
        assert result.backend == "genai"


class TestGetModelOptions:
    def test_genai_defaults(self) -> None:
        opts = get_model_options({}, "genai")
        assert len(opts["aspect_ratio"]) == 10
        assert opts["image_size"] == ["1K"]
        assert opts["size"] == []

    def test_openai_keys(self) -> None:
        model_info: dict[str, Any] = {
            "options": {
                "size": ["1024x1024"],
                "quality": ["high"],
                "background": ["opaque"],
                "style": ["vivid"],
            }
        }
        opts = get_model_options(model_info, "openai")
        assert opts["size"] == ["1024x1024"]
        assert opts["aspect_ratio"] == []

    def test_genai_custom_options(self) -> None:
        model_info: dict[str, Any] = {
            "options": {
                "aspect_ratio": ["1:1"],
                "image_size": ["4K"],
                "grounding": ["google-search"],
            }
        }
        opts = get_model_options(model_info, "genai")
        assert opts["aspect_ratio"] == ["1:1"]
        assert opts["image_size"] == ["4K"]


class TestValidateOption:
    def test_valid_option_passes(self) -> None:
        validate_option("16:9", ["1:1", "16:9"], "--aspect-ratio", "model")

    def test_invalid_option_exits(self) -> None:
        with pytest.raises(SystemExit):
            validate_option("99:1", ["1:1", "16:9"], "--aspect-ratio", "model")


class TestValidateBackendOption:
    def test_matching_backend_passes(self) -> None:
        validate_backend_option("16:9", "--aspect-ratio", "genai", "genai")

    def test_wrong_backend_exits(self) -> None:
        with pytest.raises(SystemExit):
            validate_backend_option("16:9", "--aspect-ratio", "openai", "genai")

    def test_none_value_always_passes(self) -> None:
        validate_backend_option(None, "--aspect-ratio", "openai", "genai")


class TestLoadProviders:
    def test_load_from_cwd(self, tmp_path: Path) -> None:
        _write_provider_json(tmp_path, [SAMPLE_PROVIDER])
        with patch("imagegen.provider.Path.cwd", return_value=tmp_path):
            providers = load_providers()
        assert len(providers) == 1
        assert providers[0]["name"] == "test-prov"
```

- [ ] **Step 2: Run tests**

Run: `uv run pytest tests/test_provider.py -v`
Expected: All tests pass

- [ ] **Step 3: Commit**

```bash
git add tests/test_provider.py
git commit -m "test(provider): add comprehensive tests for resolve_model and validation

Tests cover: valid/invalid specs, env var fallback, default backend,
get_model_options for both backends, validate_option, validate_backend_option,
and load_providers."
```

---

### Task 7: Add tests for `session.py`

**Files:**
- Create: `tests/test_session.py`

- [ ] **Step 1: Write tests for session management**

Create `tests/test_session.py`:

```python
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from imagegen.session import create_session, list_sessions, load_session, save_turn


@pytest.fixture()
def sessions_dir(tmp_path: Path) -> Path:
    """Patch user_config_dir so sessions are stored under tmp_path."""
    config_dir = tmp_path / "config"
    with patch("imagegen.session.user_config_dir", return_value=config_dir):
        yield config_dir


class TestCreateSession:
    def test_creates_directory_and_metadata(self, sessions_dir: Path) -> None:
        session_id, session_dir = create_session("prov/model")

        assert len(session_id) == 12
        assert session_dir.is_dir()

        meta_path = session_dir / "metadata.json"
        assert meta_path.is_file()

        metadata = json.loads(meta_path.read_text())
        assert metadata["session_id"] == session_id
        assert metadata["model_spec"] == "prov/model"
        assert metadata["turns"] == []
        assert "created_at" in metadata

    def test_unique_ids(self, sessions_dir: Path) -> None:
        id1, _ = create_session("prov/model")
        id2, _ = create_session("prov/model")
        assert id1 != id2


class TestLoadSession:
    def test_load_existing(self, sessions_dir: Path) -> None:
        session_id, _ = create_session("prov/model")
        sess_dir, metadata = load_session(session_id)

        assert sess_dir.is_dir()
        assert metadata["session_id"] == session_id

    def test_load_nonexistent_exits(self, sessions_dir: Path) -> None:
        with pytest.raises(SystemExit):
            load_session("nonexistent-id")


class TestSaveTurn:
    def test_appends_turn(self, sessions_dir: Path) -> None:
        session_id, session_dir = create_session("prov/model")

        save_turn(session_dir, 0, "draw a cat", Path("turn_000.png"))
        save_turn(session_dir, 1, "make it blue", Path("turn_001.png"), ["ref.png"])

        metadata = json.loads((session_dir / "metadata.json").read_text())
        assert len(metadata["turns"]) == 2
        assert metadata["turns"][0]["prompt"] == "draw a cat"
        assert metadata["turns"][0]["turn"] == 0
        assert metadata["turns"][1]["input_images"] == ["ref.png"]

    def test_none_image_path(self, sessions_dir: Path) -> None:
        session_id, session_dir = create_session("prov/model")
        save_turn(session_dir, 0, "hello", None)

        metadata = json.loads((session_dir / "metadata.json").read_text())
        assert metadata["turns"][0]["output_image"] is None


class TestListSessions:
    def test_empty_when_no_sessions(self, sessions_dir: Path) -> None:
        assert list_sessions() == []

    def test_lists_created_sessions(self, sessions_dir: Path) -> None:
        create_session("prov/model-a")
        create_session("prov/model-b")

        sessions = list_sessions()
        assert len(sessions) == 2
        specs = {s["model_spec"] for s in sessions}
        assert specs == {"prov/model-a", "prov/model-b"}
```

- [ ] **Step 2: Run tests**

Run: `uv run pytest tests/test_session.py -v`
Expected: All tests pass

- [ ] **Step 3: Commit**

```bash
git add tests/test_session.py
git commit -m "test(session): add tests for create, load, save_turn, and list

Tests cover: directory/metadata creation, unique IDs, loading existing
and nonexistent sessions, turn appending, and listing."
```

---

### Task 8: Add tests for genai backend

**Files:**
- Create: `tests/test_backends_genai.py`

- [ ] **Step 1: Write tests for config building and image extraction**

Create `tests/test_backends_genai.py`:

```python
from __future__ import annotations

import base64
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from imagegen.backends.genai import (
    build_config,
    build_image_config,
    extract_and_save_image,
    extract_parts,
)


class TestBuildImageConfig:
    def test_none_when_both_none(self) -> None:
        assert build_image_config(None, None) is None

    def test_returns_config_with_aspect_ratio(self) -> None:
        cfg = build_image_config("16:9", None)
        assert cfg is not None
        assert cfg.aspect_ratio == "16:9"

    def test_returns_config_with_image_size(self) -> None:
        cfg = build_image_config(None, "2K")
        assert cfg is not None
        assert cfg.image_size == "2K"

    def test_returns_config_with_both(self) -> None:
        cfg = build_image_config("1:1", "4K")
        assert cfg is not None
        assert cfg.aspect_ratio == "1:1"
        assert cfg.image_size == "4K"


class TestBuildConfig:
    def test_default_modalities(self) -> None:
        config = build_config()
        assert "IMAGE" in config.response_modalities
        assert "TEXT" in config.response_modalities

    def test_no_tools_without_grounding(self) -> None:
        config = build_config()
        assert config.tools is None

    def test_google_search_grounding(self) -> None:
        config = build_config(grounding="google-search")
        assert config.tools is not None
        assert len(config.tools) == 1

    def test_image_search_grounding(self) -> None:
        config = build_config(grounding="image-search")
        assert config.tools is not None
        assert len(config.tools) == 1


class TestExtractParts:
    def test_returns_none_for_empty_candidates(self) -> None:
        response = MagicMock()
        response.candidates = []
        assert extract_parts(response) is None

    def test_returns_none_for_none_candidates(self) -> None:
        response = MagicMock()
        response.candidates = None
        assert extract_parts(response) is None

    def test_returns_parts(self) -> None:
        part = MagicMock()
        response = MagicMock()
        response.candidates = [MagicMock()]
        response.candidates[0].content.parts = [part]
        result = extract_parts(response)
        assert result == [part]


class TestExtractAndSaveImage:
    def test_saves_bytes_image(self, tmp_path: Path) -> None:
        image_bytes = b"\x89PNG\r\n\x1a\nfakeimage"
        part = MagicMock()
        part.inline_data.data = image_bytes
        part.text = None

        response = MagicMock()
        response.candidates = [MagicMock()]
        response.candidates[0].content.parts = [part]

        output = tmp_path / "out.png"
        extract_and_save_image(response, output)

        assert output.read_bytes() == image_bytes

    def test_saves_base64_image(self, tmp_path: Path) -> None:
        raw = b"hello-image-data"
        b64 = base64.b64encode(raw).decode()

        part = MagicMock()
        part.inline_data.data = b64
        part.text = None

        response = MagicMock()
        response.candidates = [MagicMock()]
        response.candidates[0].content.parts = [part]

        output = tmp_path / "out.png"
        extract_and_save_image(response, output)

        assert output.read_bytes() == raw

    def test_exits_on_empty_response(self) -> None:
        response = MagicMock()
        response.candidates = []

        with pytest.raises(SystemExit):
            extract_and_save_image(response, Path("out.png"))

    def test_exits_when_no_image_in_parts(self) -> None:
        part = MagicMock()
        part.inline_data = None
        part.text = None

        response = MagicMock()
        response.candidates = [MagicMock()]
        response.candidates[0].content.parts = [part]

        with pytest.raises(SystemExit):
            extract_and_save_image(response, Path("out.png"))
```

- [ ] **Step 2: Run tests**

Run: `uv run pytest tests/test_backends_genai.py -v`
Expected: All tests pass

- [ ] **Step 3: Commit**

```bash
git add tests/test_backends_genai.py
git commit -m "test(backends): add tests for genai config building and image extraction

Tests cover: build_image_config, build_config with grounding options,
extract_parts null safety, extract_and_save_image for bytes/base64/errors."
```

---

### Task 9: Add tests for OpenAI backend

**Files:**
- Create: `tests/test_backends_openai.py`

- [ ] **Step 1: Write tests for client building, multi-image, and file handling**

Create `tests/test_backends_openai.py`:

```python
from __future__ import annotations

import base64
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from imagegen.backends.openai import _build_client, _save_image, generate


class TestBuildClient:
    def test_appends_v1_to_base_url(self) -> None:
        with patch("imagegen.backends.openai.OpenAI") as mock_openai:
            _build_client("key", "https://api.example.com")
            mock_openai.assert_called_once_with(
                api_key="key", base_url="https://api.example.com/v1"
            )

    def test_no_double_v1(self) -> None:
        with patch("imagegen.backends.openai.OpenAI") as mock_openai:
            _build_client("key", "https://api.example.com/v1")
            mock_openai.assert_called_once_with(
                api_key="key", base_url="https://api.example.com/v1"
            )

    def test_empty_base_url_uses_default(self) -> None:
        with patch("imagegen.backends.openai.OpenAI") as mock_openai:
            _build_client("key", "")
            mock_openai.assert_called_once_with(api_key="key")

    def test_strips_trailing_slash(self) -> None:
        with patch("imagegen.backends.openai.OpenAI") as mock_openai:
            _build_client("key", "https://api.example.com/")
            mock_openai.assert_called_once_with(
                api_key="key", base_url="https://api.example.com/v1"
            )


class TestSaveImage:
    def test_saves_decoded_image(self, tmp_path: Path) -> None:
        raw = b"fake-png-data"
        b64 = base64.b64encode(raw).decode()
        output = tmp_path / "out.png"
        _save_image(b64, output)
        assert output.read_bytes() == raw

    def test_creates_parent_dir(self, tmp_path: Path) -> None:
        raw = b"data"
        b64 = base64.b64encode(raw).decode()
        output = tmp_path / "subdir" / "out.png"
        _save_image(b64, output)
        assert output.read_bytes() == raw

    def test_exits_on_none(self) -> None:
        with pytest.raises(SystemExit):
            _save_image(None, Path("out.png"))

    def test_exits_on_empty_string(self) -> None:
        with pytest.raises(SystemExit):
            _save_image("", Path("out.png"))


class TestGenerate:
    def test_single_image(self, tmp_path: Path) -> None:
        output = tmp_path / "out.png"
        raw = b"image-data"
        b64 = base64.b64encode(raw).decode()

        mock_client = MagicMock()
        image_data = MagicMock()
        image_data.b64_json = b64
        mock_client.images.generate.return_value.data = [image_data]

        with patch("imagegen.backends.openai._build_client", return_value=mock_client):
            generate(
                prompt="a cat",
                base_url="https://api.test.com",
                model_name="model",
                api_key="key",
                output=output,
            )

        assert output.read_bytes() == raw
        mock_client.images.generate.assert_called_once()

    def test_multi_image_uses_n_param(self, tmp_path: Path) -> None:
        output = tmp_path / "out.png"
        raw1 = b"image-1"
        raw2 = b"image-2"
        b64_1 = base64.b64encode(raw1).decode()
        b64_2 = base64.b64encode(raw2).decode()

        mock_client = MagicMock()
        img1 = MagicMock()
        img1.b64_json = b64_1
        img2 = MagicMock()
        img2.b64_json = b64_2
        mock_client.images.generate.return_value.data = [img1, img2]

        with patch("imagegen.backends.openai._build_client", return_value=mock_client):
            generate(
                prompt="a cat",
                base_url="https://api.test.com",
                model_name="model",
                api_key="key",
                output=output,
                n=2,
            )

        # Only one API call with n=2
        mock_client.images.generate.assert_called_once()
        call_kwargs = mock_client.images.generate.call_args
        assert call_kwargs[1]["n"] == 2 or call_kwargs.kwargs.get("n") == 2

        # Two output files
        assert (tmp_path / "out_0.png").read_bytes() == raw1
        assert (tmp_path / "out_1.png").read_bytes() == raw2

    def test_empty_response_exits(self, tmp_path: Path) -> None:
        mock_client = MagicMock()
        mock_client.images.generate.return_value.data = []

        with (
            patch("imagegen.backends.openai._build_client", return_value=mock_client),
            pytest.raises(SystemExit),
        ):
            generate(
                prompt="a cat",
                base_url="",
                model_name="model",
                api_key="key",
                output=tmp_path / "out.png",
            )
```

- [ ] **Step 2: Run tests**

Run: `uv run pytest tests/test_backends_openai.py -v`
Expected: All tests pass

- [ ] **Step 3: Commit**

```bash
git add tests/test_backends_openai.py
git commit -m "test(backends): add tests for OpenAI client building, save, and generate

Tests cover: _build_client URL handling (v1 suffix, trailing slash, empty),
_save_image (decode, parent dir creation, error cases),
generate (single image, multi-image with n param, empty response)."
```

---

### Task 10: Sync documentation with current codebase

**Files:**
- Modify: `AGENTS.md`
- Modify: `docs/development.md`

- [ ] **Step 1: Update AGENTS.md code map**

Replace the STRUCTURE section in `AGENTS.md` with the current module layout:

```markdown
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
```

Replace the CODE MAP table:

```markdown
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
```

Replace the CALL FLOW section:

```markdown
## CALL FLOW

```
CLI generate <prompt> <model_spec> <output>
  → resolve_model(model_spec)        # "prov/model" → ResolvedModel
  → _validate_generate_options(...)  # check backend-specific options
  → backends.generate(backend, prompt, base_url, model_name, api_key, output, ...)
    → genai.generate(...) or openai.generate(...)
```
```

- [ ] **Step 2: Update `docs/development.md` directory structure**

In `docs/development.md`, find the directory structure section (around line 17-44) and update it to match the current layout:

```markdown
## 目录结构

```
imagegen/
├── pyproject.toml              # 项目元数据、依赖、入口点、构建系统配置
├── README.md                   # 用户级使用文档
├── .gitignore                  # Git 忽略规则
├── uv.lock                     # uv 锁定文件
├── docs/                       # 文档目录
│   ├── development.md          # 本文件
│   ├── configuration.md        # 配置参考
│   ├── install.md              # 安装指南
│   └── user-guide.md           # 用户指南
├── references/                 # NanoBanana 模型参考文档
├── src/
│   └── imagegen/
│       ├── __init__.py         # 包初始化 + 动态版本号 (importlib.metadata)
│       ├── __main__.py         # python -m imagegen 支持
│       ├── models.py           # ResolvedModel 数据类
│       ├── cli.py              # CLI 命令定义（click）
│       ├── provider.py         # 提供商配置加载与模型解析
│       ├── chat.py             # 多轮对话 REPL 模式
│       ├── session.py          # 会话管理（创建/加载/保存/列表）
│       ├── backends/           # 后端实现
│       │   ├── __init__.py     # 后端调度路由
│       │   ├── genai.py        # Google GenAI 后端
│       │   └── openai.py       # OpenAI 后端
│       └── provider.json.example  # 提供商配置示例文件
└── tests/
    ├── __init__.py             # 测试包初始化
    ├── test_prompt_quotes.py   # CLI 参数传递测试
    ├── test_provider.py        # 提供商配置测试
    ├── test_session.py         # 会话管理测试
    ├── test_backends_genai.py  # GenAI 后端测试
    └── test_backends_openai.py # OpenAI 后端测试
```
```

Also update the `generate.py` references in the module detail section (Section 5, around line 236). Replace the heading and content:

Old heading: `### 5. `generate.py` — 图像生成`

New heading: `### 5. `backends/` — 图像生成后端`

Update the function table to reflect the current backend structure:

```markdown
### 5. `backends/` — 图像生成后端

由三个文件组成的后端模块：

#### `backends/__init__.py` — 后端调度

| 函数 | 签名 | 职责 |
|------|------|------|
| `generate()` | `(backend, prompt, base_url, ...) -> None` | 根据 backend 路由到 genai 或 openai |
| `edit()` | `(backend, prompt, images, ...) -> None` | 根据 backend 路由编辑请求 |

#### `backends/genai.py` — Google GenAI 后端

| 函数 | 签名 | 职责 |
|------|------|------|
| `_build_grounding_tools()` | `(grounding: str \| None) -> list[types.Tool] \| None` | 构建搜索增强工具列表 |
| `build_image_config()` | `(aspect_ratio, image_size) -> types.ImageConfig \| None` | 构建图像配置 |
| `build_config()` | `(aspect_ratio, image_size, grounding) -> GenerateContentConfig` | 构建完整生成配置 |
| `extract_parts()` | `(response) -> list[types.Part] \| None` | 从响应中提取 parts（null-safe） |
| `extract_and_save_image()` | `(response, output) -> None` | 从响应中提取图像并保存 |
| `generate()` | `(prompt, base_url, ...) -> None` | 文本到图像生成 |
| `edit()` | `(prompt, images, ...) -> None` | 图像编辑（多图输入） |

#### `backends/openai.py` — OpenAI 后端

| 函数 | 签名 | 职责 |
|------|------|------|
| `_build_client()` | `(api_key, base_url) -> OpenAI` | 构建 OpenAI 客户端（自动追加 /v1） |
| `_save_image()` | `(b64_json, output) -> None` | 解码 base64 图像并保存 |
| `generate()` | `(prompt, base_url, ..., n) -> None` | 图像生成（支持 n 参数多图） |
| `edit()` | `(prompt, images, ...) -> None` | 图像编辑 |
```

- [ ] **Step 3: Run checks on modified docs**

Run: `uv run ruff check src/ && uv run mypy src/ && uv run pytest -v`
Expected: All passed (docs changes don't affect code)

- [ ] **Step 4: Commit**

```bash
git add AGENTS.md docs/development.md
git commit -m "docs: sync AGENTS.md and development.md with current codebase

- Update directory structure to include backends/ and models.py
- Replace stale generate.py references with backends/ module docs
- Update code map table with current symbols and locations
- Update call flow diagram"
```

---

### Task 11: Final verification and merge preparation

- [ ] **Step 1: Run full test suite**

Run: `uv run pytest -v`
Expected: All tests pass (should be ~30+ tests)

- [ ] **Step 2: Run full lint and type check**

Run: `uv run ruff check src/ tests/ && uv run ruff format --check src/ tests/ && uv run mypy src/`
Expected: All checks pass

- [ ] **Step 3: Verify git log**

Run: `git log --oneline develop..HEAD`
Expected: Clean sequence of conventional commits:
```
fix(backends): close mask file handle and use n param for multi-image generation
refactor(provider): replace raw tuple with ResolvedModel dataclass
refactor(backends): extract shared response parsing into extract_parts()
refactor: use importlib.metadata for dynamic version
chore: add .imagegen/ to gitignore
test(provider): add comprehensive tests for resolve_model and validation
test(session): add tests for create, load, save_turn, and list
test(backends): add tests for genai config building and image extraction
test(backends): add tests for OpenAI client building, save, and generate
docs: sync AGENTS.md and development.md with current codebase
```
