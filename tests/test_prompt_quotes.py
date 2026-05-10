from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from imagegen.cli import main
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


@pytest.mark.parametrize(
    "prompt",
    [
        "a cat's toy",
        'He said "hello"',
        'She said "it\'s wonderful"',
        "quotes 'single' and \"double\" mixed",
        'backslash \\ and "quote"',
        "中文引号「测试」和'单引号'",
        "",
        "nested \"he said 'hi'\" end",
    ],
    ids=[
        "single_quote",
        "double_quote",
        "escaped_double_in_single",
        "mixed_quotes",
        "backslash_and_quote",
        "unicode_quotes",
        "empty_prompt",
        "nested_quotes",
    ],
)
def test_generate_prompt_with_quotes(prompt: str) -> None:
    """Prompt strings with various quote characters must arrive at the backend unchanged."""
    runner = CliRunner()
    captured_prompt: list[str] = []

    def fake_generate(*, backend: str, prompt: str, **kwargs: object) -> None:  # noqa: ARG001
        captured_prompt.append(prompt)

    with (
        patch("imagegen.cli.resolve_model", return_value=FAKE_RESOLVE),
        patch("imagegen.cli.backend_generate", side_effect=fake_generate),
    ):
        result = runner.invoke(main, ["generate", prompt, "prov/model", "out.png"])

    assert result.exit_code == 0, f"CLI failed: {result.output}"
    assert len(captured_prompt) == 1
    assert captured_prompt[0] == prompt


@pytest.mark.parametrize(
    "prompt",
    [
        "edit a cat's photo",
        'make it say "cheese"',
    ],
    ids=["edit_single_quote", "edit_double_quote"],
)
def test_edit_prompt_with_quotes(prompt: str, tmp_path: Path) -> None:
    """Edit command also preserves quotes in prompts."""
    runner = CliRunner()
    captured_prompt: list[str] = []

    dummy_img = tmp_path / "dummy.png"
    dummy_img.write_bytes(b"\x89PNG\r\n\x1a\n")

    def fake_edit(*, backend: str, prompt: str, **kwargs: object) -> None:  # noqa: ARG001
        captured_prompt.append(prompt)

    with (
        patch("imagegen.cli.resolve_model", return_value=FAKE_RESOLVE),
        patch("imagegen.cli.backend_edit", side_effect=fake_edit),
    ):
        result = runner.invoke(
            main,
            ["edit", prompt, "prov/model", "out.png", "--image", str(dummy_img)],
        )

    assert result.exit_code == 0, f"CLI failed: {result.output}"
    assert len(captured_prompt) == 1
    assert captured_prompt[0] == prompt
