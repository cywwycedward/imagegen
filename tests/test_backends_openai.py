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
        call_kwargs = mock_client.images.generate.call_args.kwargs
        assert call_kwargs["n"] == 2

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
