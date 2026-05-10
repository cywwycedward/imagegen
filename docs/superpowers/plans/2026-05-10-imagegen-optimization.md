# imagegen Optimization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Improve imagegen's parameter discoverability and add a free-variable prompt template system, as specified in `docs/superpowers/specs/2026-05-10-optimization-plan-review-design.md`.

**Architecture:** Phase 1 enhances existing `provider.py` and `cli.py` with fuzzy matching and better `--options` output. Phase 2 adds a new `template.py` module with CRUD and variable substitution, integrated into `generate` and `edit` CLI commands via `--template`/`--var` options.

**Tech Stack:** Python 3, click, rich, difflib (stdlib), pytest

---

## File Structure

| File | Role | Action |
|------|------|--------|
| `src/imagegen/provider.py` | Model resolution and option validation | Modify: add `difflib` fuzzy matching to `validate_option` |
| `src/imagegen/cli.py` | CLI entry points | Modify: improve `--options` output; add `template` subcommand group; add `--template`/`--var` to `generate`/`edit` |
| `src/imagegen/template.py` | Template CRUD, variable extraction, apply logic | Create |
| `tests/test_provider.py` | Provider/validation tests | Modify: add fuzzy matching tests |
| `tests/test_template.py` | Template system tests | Create |
| `.claude/skills/imagegen-usage/SKILL.md` | Agent skill doc | Modify: remove hardcoded param values, add workflows |

---

## Phase 1: Parameter Discovery & Skill Fix

### Task 1: Add fuzzy matching to `validate_option`

**Files:**
- Modify: `src/imagegen/provider.py:128-141`
- Modify: `tests/test_provider.py`

- [ ] **Step 1: Write failing tests for fuzzy matching**

Add a new test class at the end of `tests/test_provider.py`:

```python
class TestValidateOptionFuzzyMatch:
    def test_suggestion_for_close_match(self, capsys: pytest.CaptureFixture[str]) -> None:
        with pytest.raises(SystemExit):
            validate_option("hig", ["standard", "hd", "medium"], "--quality", "gpt-image-2")
        captured = capsys.readouterr()
        assert "Did you mean:" in captured.err

    def test_no_suggestion_for_distant_match(self, capsys: pytest.CaptureFixture[str]) -> None:
        with pytest.raises(SystemExit):
            validate_option("zzzzz", ["standard", "hd", "medium"], "--quality", "gpt-image-2")
        captured = capsys.readouterr()
        assert "Did you mean:" not in captured.err

    def test_suggestion_value_is_correct(self, capsys: pytest.CaptureFixture[str]) -> None:
        with pytest.raises(SystemExit):
            validate_option("high", ["standard", "hd", "medium"], "--quality", "gpt-image-2")
        captured = capsys.readouterr()
        assert "hd" in captured.err

    def test_accepted_values_still_listed(self, capsys: pytest.CaptureFixture[str]) -> None:
        with pytest.raises(SystemExit):
            validate_option("high", ["standard", "hd", "medium"], "--quality", "gpt-image-2")
        captured = capsys.readouterr()
        assert "Accepted: standard, hd, medium" in captured.err
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /home/cywwycatari/workspace/uv/uv_tools/imagegen && uv run pytest tests/test_provider.py::TestValidateOptionFuzzyMatch -v`

Expected: FAIL — `"Did you mean:"` not in output because current `validate_option` doesn't produce suggestions.

- [ ] **Step 3: Implement fuzzy matching in `validate_option`**

Replace `validate_option` in `src/imagegen/provider.py:128-141` with:

```python
def validate_option(
    value: str,
    allowed: list[str],
    option_name: str,
    model_key: str,
) -> None:
    if value not in allowed:
        import difflib

        available = ", ".join(allowed)
        msg = (
            f"Error: {option_name} '{value}' is not supported by model '{model_key}'. "
            f"Accepted: {available}"
        )
        suggestion = difflib.get_close_matches(value, allowed, n=1, cutoff=0.4)
        if suggestion:
            msg += f"\n       Did you mean: {suggestion[0]}?"
        print(msg, file=sys.stderr)
        sys.exit(1)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /home/cywwycatari/workspace/uv/uv_tools/imagegen && uv run pytest tests/test_provider.py -v`

Expected: ALL PASS (including existing tests — the valid-option path is unchanged).

- [ ] **Step 5: Run linter and type checker**

Run: `cd /home/cywwycatari/workspace/uv/uv_tools/imagegen && uv run ruff check src/imagegen/provider.py && uv run mypy src/imagegen/provider.py`

Expected: No errors.

- [ ] **Step 6: Commit**

```bash
git add src/imagegen/provider.py tests/test_provider.py
git commit -m "feat: add fuzzy matching suggestions to validate_option"
```

---

### Task 2: Improve `provider list --options` output

**Files:**
- Modify: `src/imagegen/cli.py:55-83`

- [ ] **Step 1: Manually test current `--options` output to understand baseline**

Run: `cd /home/cywwycatari/workspace/uv/uv_tools/imagegen && uv run imagegen provider list --options`

Note the output format — all 7 parameter columns shown for every model regardless of backend.

- [ ] **Step 2: Replace the `if options:` branch in `provider_list`**

Replace `src/imagegen/cli.py:55-83` (the `if options:` block) with:

```python
    if options:
        genai_models = []
        openai_models = []
        for p in providers:
            backend = p.get("backend", "genai")
            for model_key, model_info in p.get("models", {}).items():
                opts = get_model_options(model_info, backend)
                entry = (model_key, p["name"], backend, opts)
                if backend == "openai":
                    openai_models.append(entry)
                else:
                    genai_models.append(entry)

        if genai_models:
            table = Table(show_header=True, title="GenAI Models")
            table.add_column("Model ID", style="cyan")
            table.add_column("Provider", style="green")
            table.add_column("Aspect Ratio", style="yellow")
            table.add_column("Image Size", style="yellow")
            table.add_column("Grounding", style="yellow")
            for model_key, pname, _, opts in genai_models:
                table.add_row(
                    model_key,
                    pname,
                    ", ".join(opts["aspect_ratio"]) or "-",
                    ", ".join(opts["image_size"]) or "-",
                    ", ".join(opts["grounding"]) or "-",
                )
            console.print(table)

        if openai_models:
            table = Table(show_header=True, title="OpenAI Models")
            table.add_column("Model ID", style="cyan")
            table.add_column("Provider", style="green")
            table.add_column("Size", style="yellow")
            table.add_column("Quality", style="yellow")
            table.add_column("Background", style="yellow")
            table.add_column("Style", style="yellow")
            for model_key, pname, _, opts in openai_models:
                table.add_row(
                    model_key,
                    pname,
                    ", ".join(opts["size"]) or "-",
                    ", ".join(opts["quality"]) or "-",
                    ", ".join(opts["background"]) or "-",
                    ", ".join(opts["style"]) or "-",
                )
            console.print(table)
```

- [ ] **Step 3: Manually verify improved output**

Run: `cd /home/cywwycatari/workspace/uv/uv_tools/imagegen && uv run imagegen provider list --options`

Expected: Two separate tables (one per backend type) with only relevant columns. No more `-` columns for inapplicable options.

- [ ] **Step 4: Run linter and type checker**

Run: `cd /home/cywwycatari/workspace/uv/uv_tools/imagegen && uv run ruff check src/imagegen/cli.py && uv run mypy src/imagegen/cli.py`

Expected: No errors.

- [ ] **Step 5: Run full test suite to check for regressions**

Run: `cd /home/cywwycatari/workspace/uv/uv_tools/imagegen && uv run pytest -v`

Expected: ALL PASS.

- [ ] **Step 6: Commit**

```bash
git add src/imagegen/cli.py
git commit -m "feat: improve --options output by splitting tables per backend"
```

---

### Task 3: Fix Skill document

**Files:**
- Modify: `.claude/skills/imagegen-usage/SKILL.md:55-73`

- [ ] **Step 1: Replace GenAI Backend Options section (lines 55-61)**

Replace:

```markdown
### GenAI Backend Options

| Option | Values | Notes |
|---|---|---|
| `--aspect-ratio` | `1:1`, `2:3`, `3:2`, `3:4`, `4:3`, `4:5`, `5:4`, `9:16`, `16:9`, `21:9` (+ ultra-wide for NB2) | Default depends on model config |
| `--image-size` | `1K`, `2K`, `4K` | Not all models support all sizes |
| `--grounding` | `google-search`, `image-search` | Only if model config enables it |
```

With:

```markdown
### GenAI Backend Options

Parameter values vary by model. Query before use:
`uv run imagegen provider list --options`

Available parameters: `--aspect-ratio`, `--image-size`, `--grounding`
```

- [ ] **Step 2: Replace OpenAI Backend Options section (lines 63-73)**

Replace:

```markdown
### OpenAI Backend Options

| Option | Values |
|---|---|
| `--size` | `auto`, `1024x1024`, `1536x1024`, `1024x1536` |
| `--quality` | `auto`, `low`, `medium`, `high` |
| `--background` | `auto`, `transparent`, `opaque` |
| `--style` | `vivid`, `natural` |
| `--output-format` | `png`, `jpeg`, `webp` |
| `--output-compression` | `0-100` (jpeg/webp only) |
| `--n` | `1-10` (multiple images) |
```

With:

```markdown
### OpenAI Backend Options

Parameter values vary by model. Query before use:
`uv run imagegen provider list --options`

Available parameters: `--size`, `--quality`, `--background`, `--style`,
`--output-format`, `--output-compression`, `--n`
```

- [ ] **Step 3: Add Common Workflows section before the "## Common Mistakes" section**

Insert before the `## Common Mistakes` line:

```markdown
## Common Workflows

### Iterative refinement
generate → check with Read → adjust prompt → overwrite same file

### Batch with templates
Use `--template` to maintain style consistency across multiple images.
Check available templates: `imagegen template list`

### Edit mode
Edit existing images with `edit` command + `--image` flag.

## Model Capabilities (empirical, may change with model updates)

| Capability | gpt-image-2 | gemini-2.5-flash-image | gemini-3-pro-image-preview |
|---|---|---|---|
| Chinese understanding | Fair | Good | Best |
| Grid layout | Controllable | Mostly controllable | Good |
| SDF style | Good | Fair | Good |
| Speed | ~5s | ~3s | ~15s |

```

- [ ] **Step 4: Commit**

```bash
git add .claude/skills/imagegen-usage/SKILL.md
git commit -m "fix: remove hardcoded param values from skill doc, add workflows"
```

---

## Phase 2: Free-Variable Template System

### Task 4: Create `template.py` core module with tests

**Files:**
- Create: `src/imagegen/template.py`
- Create: `tests/test_template.py`

- [ ] **Step 1: Write failing tests for template data types and `extract_variables`**

Create `tests/test_template.py`:

```python
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from imagegen.template import (
    TemplateData,
    VariableSpec,
    apply_template,
    delete_template,
    extract_variables,
    get_templates_dir,
    list_templates,
    load_template,
    save_template,
)


class TestExtractVariables:
    def test_single_variable(self) -> None:
        assert extract_variables("hello {name}") == ["name"]

    def test_multiple_variables(self) -> None:
        result = extract_variables("{a} and {b} and {c}")
        assert result == ["a", "b", "c"]

    def test_no_variables(self) -> None:
        assert extract_variables("plain text") == []

    def test_escaped_braces(self) -> None:
        assert extract_variables("{{literal}} and {real}") == ["real"]

    def test_duplicate_variables(self) -> None:
        result = extract_variables("{x} then {x} again")
        assert result == ["x"]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /home/cywwycatari/workspace/uv/uv_tools/imagegen && uv run pytest tests/test_template.py::TestExtractVariables -v`

Expected: FAIL — `ImportError: cannot import name 'extract_variables' from 'imagegen.template'`

- [ ] **Step 3: Implement `template.py` with data types and `extract_variables`**

Create `src/imagegen/template.py`:

```python
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

from imagegen.provider import user_config_dir


@dataclass(frozen=True, slots=True)
class VariableSpec:
    description: str = ""
    default: str | None = None
    required: bool = False


@dataclass(frozen=True, slots=True)
class TemplateData:
    name: str
    description: str
    template: str
    variables: dict[str, VariableSpec] = field(default_factory=dict)


_VAR_PATTERN = re.compile(r"(?<!\{)\{([a-zA-Z_][a-zA-Z0-9_]*)\}(?!\})")


def get_templates_dir() -> Path:
    return user_config_dir() / "templates"


def extract_variables(template_str: str) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for match in _VAR_PATTERN.finditer(template_str):
        name = match.group(1)
        if name not in seen:
            seen.add(name)
            result.append(name)
    return result
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /home/cywwycatari/workspace/uv/uv_tools/imagegen && uv run pytest tests/test_template.py::TestExtractVariables -v`

Expected: ALL PASS.

- [ ] **Step 5: Write failing tests for `apply_template`**

Add to `tests/test_template.py`:

```python
class TestApplyTemplate:
    def _make_template(
        self,
        template_str: str,
        variables: dict[str, VariableSpec] | None = None,
    ) -> TemplateData:
        return TemplateData(
            name="test",
            description="test template",
            template=template_str,
            variables=variables or {},
        )

    def test_basic_substitution(self) -> None:
        t = self._make_template(
            "draw {prompt} in {style}",
            {
                "prompt": VariableSpec(description="subject", required=True),
                "style": VariableSpec(description="art style", required=True),
            },
        )
        result = apply_template(t, prompt="a cat", var_overrides={"style": "watercolor"})
        assert result == "draw a cat in watercolor"

    def test_default_value_used(self) -> None:
        t = self._make_template(
            "{prompt}, {bg} background",
            {
                "prompt": VariableSpec(description="subject", required=True),
                "bg": VariableSpec(description="background", default="white"),
            },
        )
        result = apply_template(t, prompt="a tree", var_overrides={})
        assert result == "a tree, white background"

    def test_default_overridden(self) -> None:
        t = self._make_template(
            "{prompt}, {bg} background",
            {
                "prompt": VariableSpec(description="subject", required=True),
                "bg": VariableSpec(description="background", default="white"),
            },
        )
        result = apply_template(t, prompt="a tree", var_overrides={"bg": "black"})
        assert result == "a tree, black background"

    def test_missing_required_variable_raises(self) -> None:
        t = self._make_template(
            "{prompt} in {style}",
            {
                "prompt": VariableSpec(description="subject", required=True),
                "style": VariableSpec(description="art style"),
            },
        )
        with pytest.raises(SystemExit):
            apply_template(t, prompt="a cat", var_overrides={})

    def test_unknown_var_override_warns(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        t = self._make_template(
            "{prompt}",
            {"prompt": VariableSpec(description="subject", required=True)},
        )
        result = apply_template(t, prompt="a cat", var_overrides={"bogus": "val"})
        assert result == "a cat"
        captured = capsys.readouterr()
        assert "bogus" in captured.err

    def test_escaped_braces_preserved(self) -> None:
        t = self._make_template(
            "{{literal}} {prompt}",
            {"prompt": VariableSpec(description="subject", required=True)},
        )
        result = apply_template(t, prompt="test")
        assert result == "{literal} test"

    def test_prompt_auto_mapped(self) -> None:
        t = self._make_template(
            "render {prompt} nicely",
            {"prompt": VariableSpec(description="subject", required=True)},
        )
        result = apply_template(t, prompt="a dog", var_overrides={})
        assert result == "render a dog nicely"
```

- [ ] **Step 6: Run tests to verify they fail**

Run: `cd /home/cywwycatari/workspace/uv/uv_tools/imagegen && uv run pytest tests/test_template.py::TestApplyTemplate -v`

Expected: FAIL — `apply_template` not yet implemented (only stub import exists).

- [ ] **Step 7: Implement `apply_template`**

Add to `src/imagegen/template.py`:

```python
import sys


def apply_template(
    template_data: TemplateData,
    prompt: str,
    var_overrides: dict[str, str] | None = None,
) -> str:
    overrides = var_overrides or {}
    values: dict[str, str] = {}

    # Auto-map CLI prompt to {prompt} variable
    if "prompt" in template_data.variables:
        values["prompt"] = prompt

    # Apply overrides and defaults
    for var_name, spec in template_data.variables.items():
        if var_name in overrides:
            values[var_name] = overrides[var_name]
        elif var_name not in values:
            if spec.default is not None:
                values[var_name] = spec.default
            elif spec.required or spec.default is None:
                print(
                    f"Error: template '{template_data.name}' requires variable "
                    f"'{var_name}' but it was not provided.\n"
                    f"       Description: {spec.description}",
                    file=sys.stderr,
                )
                sys.exit(1)

    # Warn about unknown overrides
    defined = set(template_data.variables.keys())
    for key in overrides:
        if key not in defined:
            all_vars = ", ".join(defined)
            print(
                f"Warning: template '{template_data.name}' does not define "
                f"variable '{key}'.\n"
                f"         Defined variables: {all_vars}",
                file=sys.stderr,
            )

    # Substitute variables, then unescape {{ / }}
    result = template_data.template
    for var_name, val in values.items():
        result = result.replace("{" + var_name + "}", val)
    result = result.replace("{{", "{").replace("}}", "}")

    return result
```

- [ ] **Step 8: Run tests to verify they pass**

Run: `cd /home/cywwycatari/workspace/uv/uv_tools/imagegen && uv run pytest tests/test_template.py -v`

Expected: ALL PASS.

- [ ] **Step 9: Run linter and type checker**

Run: `cd /home/cywwycatari/workspace/uv/uv_tools/imagegen && uv run ruff check src/imagegen/template.py tests/test_template.py && uv run mypy src/imagegen/template.py`

Expected: No errors.

- [ ] **Step 10: Commit**

```bash
git add src/imagegen/template.py tests/test_template.py
git commit -m "feat: add template core — data types, extract_variables, apply_template"
```

---

### Task 5: Add template CRUD operations with tests

**Files:**
- Modify: `src/imagegen/template.py`
- Modify: `tests/test_template.py`

- [ ] **Step 1: Write failing tests for CRUD operations**

Add to `tests/test_template.py`:

```python
class TestTemplateCRUD:
    def test_save_and_load(self, tmp_path: Path) -> None:
        with patch("imagegen.template.get_templates_dir", return_value=tmp_path):
            save_template(
                name="my-tpl",
                template_str="draw {prompt} in {style}",
                description="test template",
                variables={
                    "prompt": VariableSpec(description="subject", required=True),
                    "style": VariableSpec(description="art style", default="oil"),
                },
            )
            loaded = load_template("my-tpl")

        assert loaded.name == "my-tpl"
        assert loaded.description == "test template"
        assert loaded.template == "draw {prompt} in {style}"
        assert loaded.variables["prompt"].required is True
        assert loaded.variables["style"].default == "oil"

    def test_load_nonexistent_exits(self, tmp_path: Path) -> None:
        with patch("imagegen.template.get_templates_dir", return_value=tmp_path):
            with pytest.raises(SystemExit):
                load_template("nope")

    def test_list_templates_empty(self, tmp_path: Path) -> None:
        with patch("imagegen.template.get_templates_dir", return_value=tmp_path):
            assert list_templates() == []

    def test_list_templates_returns_summaries(self, tmp_path: Path) -> None:
        with patch("imagegen.template.get_templates_dir", return_value=tmp_path):
            save_template(
                name="tpl-a",
                template_str="{prompt}",
                description="first",
                variables={"prompt": VariableSpec(description="s", required=True)},
            )
            save_template(
                name="tpl-b",
                template_str="{prompt} {x}",
                description="second",
                variables={
                    "prompt": VariableSpec(description="s", required=True),
                    "x": VariableSpec(description="extra", default="y"),
                },
            )
            result = list_templates()

        names = [t["name"] for t in result]
        assert "tpl-a" in names
        assert "tpl-b" in names

    def test_delete_template(self, tmp_path: Path) -> None:
        with patch("imagegen.template.get_templates_dir", return_value=tmp_path):
            save_template(
                name="to-delete",
                template_str="{prompt}",
                description="will be deleted",
                variables={"prompt": VariableSpec(description="s", required=True)},
            )
            delete_template("to-delete")
            assert list_templates() == []

    def test_delete_nonexistent_exits(self, tmp_path: Path) -> None:
        with patch("imagegen.template.get_templates_dir", return_value=tmp_path):
            with pytest.raises(SystemExit):
                delete_template("ghost")
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /home/cywwycatari/workspace/uv/uv_tools/imagegen && uv run pytest tests/test_template.py::TestTemplateCRUD -v`

Expected: FAIL — `save_template`, `load_template`, `list_templates`, `delete_template` not yet implemented.

- [ ] **Step 3: Implement CRUD functions in `template.py`**

Add to `src/imagegen/template.py`:

```python
def save_template(
    name: str,
    template_str: str,
    description: str,
    variables: dict[str, VariableSpec],
) -> None:
    templates_dir = get_templates_dir()
    templates_dir.mkdir(parents=True, exist_ok=True)

    data = {
        "name": name,
        "description": description,
        "variables": {
            k: _variable_to_dict(v) for k, v in variables.items()
        },
        "template": template_str,
    }
    path = templates_dir / f"{name}.json"
    path.write_text(json.dumps(data, indent=4, ensure_ascii=False))


def load_template(name: str) -> TemplateData:
    path = get_templates_dir() / f"{name}.json"
    if not path.is_file():
        print(f"Error: template '{name}' not found.", file=sys.stderr)
        sys.exit(1)

    raw = json.loads(path.read_text())
    variables = {
        k: VariableSpec(
            description=v.get("description", ""),
            default=v.get("default"),
            required=v.get("required", False),
        )
        for k, v in raw.get("variables", {}).items()
    }
    # Mark variables without default and without explicit required as required
    final_vars: dict[str, VariableSpec] = {}
    for k, v in variables.items():
        if not v.required and v.default is None:
            final_vars[k] = VariableSpec(
                description=v.description, default=None, required=True
            )
        else:
            final_vars[k] = v

    return TemplateData(
        name=raw["name"],
        description=raw.get("description", ""),
        template=raw["template"],
        variables=final_vars,
    )


def list_templates() -> list[dict[str, str]]:
    templates_dir = get_templates_dir()
    if not templates_dir.is_dir():
        return []

    result = []
    for path in sorted(templates_dir.glob("*.json")):
        try:
            raw = json.loads(path.read_text())
            var_names = list(raw.get("variables", {}).keys())
            result.append({
                "name": raw.get("name", path.stem),
                "description": raw.get("description", ""),
                "variables": ", ".join(var_names),
            })
        except (json.JSONDecodeError, KeyError):
            continue
    return result


def delete_template(name: str) -> None:
    path = get_templates_dir() / f"{name}.json"
    if not path.is_file():
        print(f"Error: template '{name}' not found.", file=sys.stderr)
        sys.exit(1)
    path.unlink()


def _variable_to_dict(spec: VariableSpec) -> dict[str, object]:
    d: dict[str, object] = {"description": spec.description}
    if spec.required:
        d["required"] = True
    if spec.default is not None:
        d["default"] = spec.default
    return d
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /home/cywwycatari/workspace/uv/uv_tools/imagegen && uv run pytest tests/test_template.py -v`

Expected: ALL PASS.

- [ ] **Step 5: Run linter and type checker**

Run: `cd /home/cywwycatari/workspace/uv/uv_tools/imagegen && uv run ruff check src/imagegen/template.py tests/test_template.py && uv run mypy src/imagegen/template.py`

Expected: No errors.

- [ ] **Step 6: Commit**

```bash
git add src/imagegen/template.py tests/test_template.py
git commit -m "feat: add template CRUD — save, load, list, delete"
```

---

### Task 6: Add `template` CLI subcommand group

**Files:**
- Modify: `src/imagegen/cli.py`

- [ ] **Step 1: Add imports at the top of `cli.py`**

Add to the imports section at `src/imagegen/cli.py:13-21`:

```python
from imagegen.template import (
    VariableSpec,
    apply_template,
    delete_template,
    extract_variables,
    list_templates,
    load_template,
    save_template,
)
```

- [ ] **Step 2: Add the `template` subcommand group after the `provider_sessions` function**

Insert after `provider_sessions` (after line 459) in `src/imagegen/cli.py`:

```python
@main.group()
def template() -> None:
    pass


@template.command(name="list")
def template_list() -> None:
    console = Console()
    templates = list_templates()

    if not templates:
        console.print("[yellow]No templates found.[/yellow]")
        return

    table = Table(show_header=True)
    table.add_column("Name", style="cyan")
    table.add_column("Description", style="green")
    table.add_column("Variables", style="yellow")
    for t in templates:
        table.add_row(t["name"], t["description"], t["variables"])
    console.print(table)


@template.command(name="show")
@click.argument("name")
def template_show(name: str) -> None:
    console = Console()
    t = load_template(name)

    console.print(f"[cyan]Template:[/cyan] {t.name}")
    console.print(f"[green]Description:[/green] {t.description}")
    console.print()

    table = Table(show_header=True, title="Variables")
    table.add_column("Variable", style="cyan")
    table.add_column("Status", style="yellow")
    table.add_column("Description", style="green")
    for var_name, spec in t.variables.items():
        if spec.required:
            status = "(required)"
        elif spec.default is not None:
            status = f"default={spec.default}"
        else:
            status = "(required)"
        table.add_row(f"{{{var_name}}}", status, spec.description)
    console.print(table)

    console.print()
    console.print("[dim]Template string:[/dim]")
    console.print(f"  {t.template}")


@template.command(name="save")
@click.argument("name")
@click.option("--template", "template_str", required=True, help="Template string with {variable} placeholders")
@click.option("--description", default="", help="Template description")
@click.option("--var", "vars_raw", multiple=True, help="Variable spec: 'name|description' or 'name|description|default'")
def template_save(name: str, template_str: str, description: str, vars_raw: tuple[str, ...]) -> None:
    variables: dict[str, VariableSpec] = {}

    for raw in vars_raw:
        parts = raw.split("|")
        if len(parts) < 2:
            print(f"Error: --var must be 'name|description' or 'name|description|default', got: {raw}", file=sys.stderr)
            sys.exit(1)
        var_name = parts[0].strip()
        var_desc = parts[1].strip()
        var_default = parts[2].strip() if len(parts) >= 3 else None
        variables[var_name] = VariableSpec(
            description=var_desc,
            default=var_default,
            required=var_default is None,
        )

    # Auto-create required stubs for variables in template but not in --var
    for var_name in extract_variables(template_str):
        if var_name not in variables:
            variables[var_name] = VariableSpec(description="", required=True)

    save_template(name, template_str, description, variables)
    Console().print(f"[green]Template '{name}' saved.[/green]")


@template.command(name="delete")
@click.argument("name")
def template_delete(name: str) -> None:
    delete_template(name)
    Console().print(f"[green]Template '{name}' deleted.[/green]")
```

- [ ] **Step 3: Manually test the template commands**

Run:
```bash
cd /home/cywwycatari/workspace/uv/uv_tools/imagegen
uv run imagegen template list
uv run imagegen template save test-tpl \
  --template "draw {prompt} in {style}" \
  --description "test" \
  --var "prompt|The subject" \
  --var "style|Art style|watercolor"
uv run imagegen template list
uv run imagegen template show test-tpl
uv run imagegen template delete test-tpl
uv run imagegen template list
```

Expected: list shows empty → save succeeds → list shows test-tpl → show displays variables → delete succeeds → list shows empty again.

- [ ] **Step 4: Run linter and type checker**

Run: `cd /home/cywwycatari/workspace/uv/uv_tools/imagegen && uv run ruff check src/imagegen/cli.py && uv run mypy src/imagegen/cli.py`

Expected: No errors.

- [ ] **Step 5: Run full test suite**

Run: `cd /home/cywwycatari/workspace/uv/uv_tools/imagegen && uv run pytest -v`

Expected: ALL PASS.

- [ ] **Step 6: Commit**

```bash
git add src/imagegen/cli.py
git commit -m "feat: add template CLI subcommands — list, show, save, delete"
```

---

### Task 7: Integrate `--template` and `--var` into `generate` and `edit`

**Files:**
- Modify: `src/imagegen/cli.py:148-246` (generate command) and `src/imagegen/cli.py:249-365` (edit command)

- [ ] **Step 1: Add `--template` and `--var` options to the `generate` command**

Add two decorators before the `generate` function (after the `--style` option, before `def generate(`):

```python
@click.option(
    "--template",
    "template_name",
    default=None,
    help="Apply a saved prompt template",
)
@click.option(
    "--var",
    "var_overrides_raw",
    multiple=True,
    help="Override template variable: key=value",
)
```

Update the `generate` function signature to include the new parameters:

```python
def generate(
    prompt: str,
    model_spec: str,
    output: str,
    aspect_ratio: str | None,
    image_size: str | None,
    grounding: str | None,
    size: str | None,
    quality: str | None,
    background: str | None,
    output_format: str | None,
    output_compression: int | None,
    num_images: int | None,
    style: str | None,
    template_name: str | None,
    var_overrides_raw: tuple[str, ...],
) -> None:
```

Add template processing at the beginning of the function body, before `model = resolve_model(...)`:

```python
    if template_name is not None:
        tpl = load_template(template_name)
        overrides: dict[str, str] = {}
        for raw in var_overrides_raw:
            if "=" not in raw:
                print(f"Error: --var must be 'key=value', got: {raw}", file=sys.stderr)
                sys.exit(1)
            k, v = raw.split("=", maxsplit=1)
            overrides[k.strip()] = v.strip()
        prompt = apply_template(tpl, prompt=prompt, var_overrides=overrides)
```

- [ ] **Step 2: Add `--template` and `--var` options to the `edit` command**

Same pattern: add the two decorators and update the `edit` function signature similarly, then add the same template processing block at the beginning of the function body.

```python
@click.option(
    "--template",
    "template_name",
    default=None,
    help="Apply a saved prompt template",
)
@click.option(
    "--var",
    "var_overrides_raw",
    multiple=True,
    help="Override template variable: key=value",
)
```

Update `edit` signature to add `template_name: str | None` and `var_overrides_raw: tuple[str, ...]`.

Add the same template processing block at the start of the `edit` function body, before `model = resolve_model(...)`.

- [ ] **Step 3: Add `load_template` and `apply_template` to the imports if not already present**

Verify that `load_template` and `apply_template` are in the imports added in Task 6 Step 1. They should already be there.

- [ ] **Step 4: Run linter and type checker**

Run: `cd /home/cywwycatari/workspace/uv/uv_tools/imagegen && uv run ruff check src/imagegen/cli.py && uv run mypy src/imagegen/cli.py`

Expected: No errors.

- [ ] **Step 5: Run full test suite**

Run: `cd /home/cywwycatari/workspace/uv/uv_tools/imagegen && uv run pytest -v`

Expected: ALL PASS.

- [ ] **Step 6: Commit**

```bash
git add src/imagegen/cli.py
git commit -m "feat: integrate --template and --var into generate and edit commands"
```

---

### Task 8: Final integration test and cleanup

**Files:**
- All modified files

- [ ] **Step 1: Run full test suite**

Run: `cd /home/cywwycatari/workspace/uv/uv_tools/imagegen && uv run pytest -v`

Expected: ALL PASS.

- [ ] **Step 2: Run linter on all source files**

Run: `cd /home/cywwycatari/workspace/uv/uv_tools/imagegen && uv run ruff check src/ tests/`

Expected: No errors.

- [ ] **Step 3: Run type checker on all source files**

Run: `cd /home/cywwycatari/workspace/uv/uv_tools/imagegen && uv run mypy src/`

Expected: No errors.

- [ ] **Step 4: Manual end-to-end smoke test (template workflow)**

Run:
```bash
cd /home/cywwycatari/workspace/uv/uv_tools/imagegen

# Save a template
uv run imagegen template save sdf-circle \
  --template "solid {fill_color} filled circle with white cutout symbol of {prompt}, {bg_color} background, SDF style." \
  --description "SDF circular icon" \
  --var "prompt|The main subject" \
  --var "fill_color|Fill color|black" \
  --var "bg_color|Background color|pure white"

# Verify it saved
uv run imagegen template show sdf-circle

# Verify --help shows --template and --var
uv run imagegen generate --help | grep -E "template|var"

# Clean up
uv run imagegen template delete sdf-circle
```

Expected: Template saves, shows with correct variables, `--help` lists `--template` and `--var` options, deletes cleanly.

- [ ] **Step 5: Commit any final adjustments (if needed)**

Only if Steps 1-4 revealed issues that needed fixes.
