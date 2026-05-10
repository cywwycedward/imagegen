from __future__ import annotations

import base64
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from imagegen.backends.genai import (
    build_config,
    build_image_config,
    extract_and_save_image,
    extract_parts,
    generate,
    edit,
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



class TestGenerateApiError:
    def test_api_error_exits_gracefully(self, tmp_path: Path) -> None:
        """API errors should be caught and produce a clean error message, not a traceback."""
        with patch("imagegen.backends.genai.genai") as mock_genai:
            mock_client = MagicMock()
            mock_genai.Client.return_value = mock_client
            mock_client.models.generate_content.side_effect = Exception(
                "500 Server Error"
            )

            with pytest.raises(SystemExit):
                generate(
                    prompt="test",
                    base_url="https://api.test.com",
                    model_name="model",
                    api_key="key",
                    output=tmp_path / "out.png",
                )


class TestEditApiError:
    def test_api_error_exits_gracefully(self, tmp_path: Path) -> None:
        """API errors should be caught and produce a clean error message, not a traceback."""
        from PIL import Image as PILImage

        dummy_img = tmp_path / "input.png"
        PILImage.new("RGB", (1, 1), color="red").save(dummy_img)

        with patch("imagegen.backends.genai.genai") as mock_genai:
            mock_client = MagicMock()
            mock_genai.Client.return_value = mock_client
            mock_client.models.generate_content.side_effect = Exception(
                "500 Server Error"
            )

            with pytest.raises(SystemExit):
                edit(
                    prompt="test",
                    images=[dummy_img],
                    base_url="https://api.test.com",
                    model_name="model",
                    api_key="key",
                    output=tmp_path / "out.png",
                )
