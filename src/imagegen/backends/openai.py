from __future__ import annotations

import base64
import sys
from io import BufferedReader
from pathlib import Path
from typing import Any

from openai import OpenAI


def _build_client(api_key: str, base_url: str) -> OpenAI:
    if base_url:
        # OpenAI SDK replaces entire default base_url; ensure /v1 suffix
        # so requests hit /v1/images/generations (not /images/generations).
        url = base_url.rstrip("/")
        if not url.endswith("/v1"):
            url += "/v1"
        return OpenAI(api_key=api_key, base_url=url)
    return OpenAI(api_key=api_key)


def _save_image(b64_json: str | None, output: Path) -> None:
    if not b64_json:
        print("Error: no image data in response.", file=sys.stderr)
        sys.exit(1)
    image_bytes = base64.b64decode(b64_json)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(image_bytes)
    print(f"Image saved to {output}")


def generate(
    prompt: str,
    base_url: str,
    model_name: str,
    api_key: str,
    output: Path,
    size: str | None = None,
    quality: str | None = None,
    background: str | None = None,
    output_format: str | None = None,
    output_compression: int | None = None,
    n: int | None = None,
    style: str | None = None,
) -> None:
    client = _build_client(api_key, base_url)

    kwargs: dict[str, Any] = {
        "model": model_name,
        "prompt": prompt,
        "response_format": "b64_json",
    }
    if size is not None:
        kwargs["size"] = size
    if quality is not None:
        kwargs["quality"] = quality
    if background is not None:
        kwargs["background"] = background
    if output_format is not None:
        kwargs["output_format"] = output_format
    if output_compression is not None:
        kwargs["output_compression"] = output_compression
    if style is not None:
        kwargs["style"] = style

    num_images = n if n is not None else 1

    for i in range(num_images):
        response = client.images.generate(**kwargs)
        image_data = response.data[0] if response.data else None
        if image_data is None:
            print("Error: empty response from API.", file=sys.stderr)
            sys.exit(1)

        if num_images == 1:
            target = output
        else:
            target = output.parent / f"{output.stem}_{i}{output.suffix}"

        _save_image(image_data.b64_json, target)


def edit(
    prompt: str,
    images: list[Path],
    base_url: str,
    model_name: str,
    api_key: str,
    output: Path,
    size: str | None = None,
    quality: str | None = None,
    background: str | None = None,
    output_format: str | None = None,
    output_compression: int | None = None,
    n: int | None = None,
    mask: str | None = None,
    input_fidelity: str | None = None,
) -> None:
    client = _build_client(api_key, base_url)

    if not images:
        print("Error: at least one image is required for editing.", file=sys.stderr)
        sys.exit(1)

    image_files: list[BufferedReader] = [open(img, "rb") for img in images]  # noqa: SIM115

    try:
        kwargs: dict[str, Any] = {
            "model": model_name,
            "prompt": prompt,
            "image": image_files if len(image_files) > 1 else image_files[0],
            "response_format": "b64_json",
        }
        if size is not None:
            kwargs["size"] = size
        if quality is not None:
            kwargs["quality"] = quality
        if background is not None:
            kwargs["background"] = background
        if output_format is not None:
            kwargs["output_format"] = output_format
        if output_compression is not None:
            kwargs["output_compression"] = output_compression
        if mask is not None:
            kwargs["mask"] = open(mask, "rb")  # noqa: SIM115
        if input_fidelity is not None:
            kwargs["input_fidelity"] = input_fidelity

        num_images = n if n is not None else 1

        for i in range(num_images):
            response = client.images.edit(**kwargs)
            image_data = response.data[0] if response.data else None
            if image_data is None:
                print("Error: empty response from API.", file=sys.stderr)
                sys.exit(1)

            if num_images == 1:
                target = output
            else:
                target = output.parent / f"{output.stem}_{i}{output.suffix}"

            _save_image(image_data.b64_json, target)
    finally:
        for f in image_files:
            f.close()
