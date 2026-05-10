from __future__ import annotations

import json
import platform
import shutil
import sys
from importlib import resources
from pathlib import Path
from typing import Any

from imagegen.models import ResolvedModel


PROVIDER_FILENAME = "provider.json"
EXAMPLE_FILENAME = "provider.json.example"
APP_NAME = "imagegen"

GENAI_OPTION_KEYS = ("aspect_ratio", "image_size", "grounding")
OPENAI_OPTION_KEYS = ("size", "quality", "background", "style")
ALL_OPTION_KEYS = (*GENAI_OPTION_KEYS, *OPENAI_OPTION_KEYS)

DEFAULT_ASPECT_RATIOS = [
    "1:1",
    "2:3",
    "3:2",
    "3:4",
    "4:3",
    "4:5",
    "5:4",
    "9:16",
    "16:9",
    "21:9",
]
DEFAULT_IMAGE_SIZES = ["1K"]


def user_config_dir() -> Path:
    if platform.system() == "Windows":
        base = Path.home() / "AppData" / "Roaming"
    else:
        base = Path.home() / ".config"
    return base / APP_NAME


def _find_provider_file() -> Path:
    local_path = Path.cwd() / ".imagegen" / PROVIDER_FILENAME
    if local_path.is_file():
        return local_path

    user_path = user_config_dir() / PROVIDER_FILENAME
    if user_path.is_file():
        return user_path

    user_path = ensure_user_config()
    return user_path


def _get_example_path() -> Path:
    ref = resources.files(APP_NAME).joinpath(EXAMPLE_FILENAME)
    return Path(str(ref))


def ensure_user_config() -> Path:
    user_dir = user_config_dir()
    user_path = user_dir / PROVIDER_FILENAME

    if user_path.is_file():
        return user_path

    example = _get_example_path()
    if not example.is_file():
        print(
            f"Error: bundled {EXAMPLE_FILENAME} not found in package.",
            file=sys.stderr,
        )
        sys.exit(1)

    user_dir.mkdir(parents=True, exist_ok=True)
    _ = shutil.copy2(example, user_path)

    msg = (
        f"Created default configuration at:\n"
        f"  {user_path}\n"
        f"\n"
        f"Please edit this file to add your provider details (baseUrl, apiKey, models).\n"
        f"  Example:\n"
        f"    {example}\n"
    )
    print(msg, file=sys.stderr)
    return user_path


def load_providers() -> list[dict[str, Any]]:
    path = _find_provider_file()
    with path.open() as f:
        data = json.load(f)
    return data.get("providers", [])


def get_model_options(
    model_info: dict[str, Any],
    backend: str = "genai",
) -> dict[str, list[str]]:
    options: dict[str, Any] = model_info.get("options", {})

    if backend == "openai":
        return {
            "aspect_ratio": [],
            "image_size": [],
            "grounding": [],
            "size": options.get("size", []),
            "quality": options.get("quality", []),
            "background": options.get("background", []),
            "style": options.get("style", []),
        }

    return {
        "aspect_ratio": options.get("aspect_ratio", DEFAULT_ASPECT_RATIOS),
        "image_size": options.get("image_size", DEFAULT_IMAGE_SIZES),
        "grounding": options.get("grounding", []),
        "size": [],
        "quality": [],
        "background": [],
        "style": [],
    }


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


def validate_backend_option(
    value: object,
    option_name: str,
    backend: str,
    expected_backend: str,
) -> None:
    if value is not None and backend != expected_backend:
        print(
            f"Error: {option_name} is not supported by {backend} backend. "
            f"This option is only available for {expected_backend} models.",
            file=sys.stderr,
        )
        sys.exit(1)


def resolve_model(
    provider_model: str,
) -> ResolvedModel:
    parts = provider_model.split("/", maxsplit=1)
    if len(parts) != 2:
        print(
            f"Error: model must be in 'provider_name/model_name' format, got '{provider_model}'",
            file=sys.stderr,
        )
        sys.exit(1)

    provider_name, model_key = parts
    providers = load_providers()

    provider = next((p for p in providers if p["name"] == provider_name), None)
    if provider is None:
        available = ", ".join(p["name"] for p in providers)
        print(
            f"Error: provider '{provider_name}' not found. Available: {available}",
            file=sys.stderr,
        )
        sys.exit(1)

    models: dict[str, Any] = provider.get("models", {})
    if model_key not in models:
        available = ", ".join(models.keys())
        print(
            f"Error: model '{model_key}' not found in provider '{provider_name}'. Available: {available}",
            file=sys.stderr,
        )
        sys.exit(1)

    model_info = models[model_key]
    backend = provider.get("backend", "genai")
    options = get_model_options(model_info, backend)

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
