from __future__ import annotations

import sys
from pathlib import Path


def generate(
    backend: str,
    prompt: str,
    base_url: str,
    model_name: str,
    api_key: str,
    output: Path,
    *,
    aspect_ratio: str | None = None,
    image_size: str | None = None,
    grounding: str | None = None,
    size: str | None = None,
    quality: str | None = None,
    background: str | None = None,
    output_format: str | None = None,
    output_compression: int | None = None,
    n: int | None = None,
    style: str | None = None,
) -> None:
    if backend == "genai":
        from imagegen.backends import genai as _genai

        _genai.generate(
            prompt=prompt,
            base_url=base_url,
            model_name=model_name,
            api_key=api_key,
            output=output,
            aspect_ratio=aspect_ratio,
            image_size=image_size,
            grounding=grounding,
        )
    elif backend == "openai":
        from imagegen.backends import openai as _openai

        _openai.generate(
            prompt=prompt,
            base_url=base_url,
            model_name=model_name,
            api_key=api_key,
            output=output,
            size=size,
            quality=quality,
            background=background,
            output_format=output_format,
            output_compression=output_compression,
            n=n,
            style=style,
        )
    else:
        print(f"Error: unknown backend '{backend}'.", file=sys.stderr)
        sys.exit(1)


def edit(
    backend: str,
    prompt: str,
    images: list[Path],
    base_url: str,
    model_name: str,
    api_key: str,
    output: Path,
    *,
    aspect_ratio: str | None = None,
    image_size: str | None = None,
    grounding: str | None = None,
    size: str | None = None,
    quality: str | None = None,
    background: str | None = None,
    output_format: str | None = None,
    output_compression: int | None = None,
    n: int | None = None,
    mask: str | None = None,
    input_fidelity: str | None = None,
) -> None:
    if backend == "genai":
        from imagegen.backends import genai as _genai

        _genai.edit(
            prompt=prompt,
            images=images,
            base_url=base_url,
            model_name=model_name,
            api_key=api_key,
            output=output,
            aspect_ratio=aspect_ratio,
            image_size=image_size,
            grounding=grounding,
        )
    elif backend == "openai":
        from imagegen.backends import openai as _openai

        _openai.edit(
            prompt=prompt,
            images=images,
            base_url=base_url,
            model_name=model_name,
            api_key=api_key,
            output=output,
            size=size,
            quality=quality,
            background=background,
            output_format=output_format,
            output_compression=output_compression,
            n=n,
            mask=mask,
            input_fidelity=input_fidelity,
        )
    else:
        print(f"Error: unknown backend '{backend}'.", file=sys.stderr)
        sys.exit(1)
