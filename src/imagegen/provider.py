from __future__ import annotations

import json
import platform
import shutil
import sys
from importlib import resources
from pathlib import Path
from typing import Any


PROVIDER_FILENAME = "provider.json"
EXAMPLE_FILENAME = "provider.json.example"
APP_NAME = "imagegen"


def _user_config_dir() -> Path:
    """Return the platform-specific user configuration directory for imagegen.

    - Linux / macOS: ~/.config/imagegen
    - Windows:       %APPDATA%/imagegen  (e.g. C:/Users/<user>/AppData/Roaming/imagegen)
    """
    if platform.system() == "Windows":
        base = Path.home() / "AppData" / "Roaming"
    else:
        base = Path.home() / ".config"
    return base / APP_NAME


def _find_provider_file() -> Path:
    """Locate provider.json using a two-level fallback with auto-setup.

    1. Project-local:  <CWD>/.imagegen/provider.json
    2. User config:    <user_config_dir>/provider.json  (platform-dependent)
       → If missing, copies provider.json.example here on first run.
    """
    # Level 1 — project-local
    local_path = Path.cwd() / ".imagegen" / PROVIDER_FILENAME
    if local_path.is_file():
        return local_path

    # Level 2 — user config directory
    user_path = _user_config_dir() / PROVIDER_FILENAME
    if user_path.is_file():
        return user_path

    # Level 2 miss → first-run: copy example to user config dir
    user_path = ensure_user_config()
    return user_path


def _get_example_path() -> Path:
    ref = resources.files(APP_NAME).joinpath(EXAMPLE_FILENAME)
    return Path(str(ref))


def ensure_user_config() -> Path:
    """Copy provider.json.example to the user config dir if provider.json is absent."""
    user_dir = _user_config_dir()
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


def resolve_model(provider_model: str) -> tuple[str, str, str, str]:
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

    return provider["baseUrl"], model_key, models[model_key]["name"], provider["apiKey"]
