from __future__ import annotations

import json
import re
import sys
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


def _variable_to_dict(spec: VariableSpec) -> dict[str, object]:
    d: dict[str, object] = {"description": spec.description}
    if spec.required:
        d["required"] = True
    if spec.default is not None:
        d["default"] = spec.default
    return d


def _validate_template_name(name: str) -> None:
    if "/" in name or "\\" in name or ".." in name:
        print(
            f"Error: invalid template name '{name}'. "
            "Names must not contain '/', '\\', or '..'.",
            file=sys.stderr,
        )
        sys.exit(1)


def save_template(
    name: str,
    template_str: str,
    description: str,
    variables: dict[str, VariableSpec],
) -> None:
    _validate_template_name(name)
    templates_dir = get_templates_dir()
    templates_dir.mkdir(parents=True, exist_ok=True)

    data = {
        "name": name,
        "description": description,
        "variables": {k: _variable_to_dict(v) for k, v in variables.items()},
        "template": template_str,
    }
    path = templates_dir / f"{name}.json"
    path.write_text(json.dumps(data, indent=4, ensure_ascii=False))


def load_template(name: str) -> TemplateData:
    _validate_template_name(name)
    path = get_templates_dir() / f"{name}.json"
    if not path.is_file():
        print(f"Error: template '{name}' not found.", file=sys.stderr)
        sys.exit(1)

    raw = json.loads(path.read_text())
    variables: dict[str, VariableSpec] = {}
    for k, v in raw.get("variables", {}).items():
        spec = VariableSpec(
            description=v.get("description", ""),
            default=v.get("default"),
            required=v.get("required", False),
        )
        # Variables without default and without explicit required=True are treated as required
        if not spec.required and spec.default is None:
            spec = VariableSpec(description=spec.description, default=None, required=True)
        variables[k] = spec

    return TemplateData(
        name=raw["name"],
        description=raw.get("description", ""),
        template=raw["template"],
        variables=variables,
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
    _validate_template_name(name)
    path = get_templates_dir() / f"{name}.json"
    if not path.is_file():
        print(f"Error: template '{name}' not found.", file=sys.stderr)
        sys.exit(1)
    path.unlink()
