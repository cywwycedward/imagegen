from __future__ import annotations

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
