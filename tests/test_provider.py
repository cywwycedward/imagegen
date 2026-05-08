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
