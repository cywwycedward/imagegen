from __future__ import annotations

import base64
import sys
from pathlib import Path

from collections.abc import Callable
from typing import Any

from google import genai
from google.genai import types
from PIL import Image


def _build_grounding_tools(
    grounding: str | None,
) -> list[types.Tool | Callable[..., Any]] | None:
    if grounding is None:
        return None
    if grounding == "image-search":
        return [
            types.Tool(
                google_search=types.GoogleSearch(
                    search_types=types.SearchTypes(
                        web_search=types.WebSearch(),
                        image_search=types.ImageSearch(),
                    ),
                ),
            ),
        ]
    return [types.Tool(google_search=types.GoogleSearch())]


def build_image_config(
    aspect_ratio: str | None,
    image_size: str | None,
) -> types.ImageConfig | None:
    if aspect_ratio is None and image_size is None:
        return None
    return types.ImageConfig(aspect_ratio=aspect_ratio, image_size=image_size)


def build_config(
    aspect_ratio: str | None = None,
    image_size: str | None = None,
    grounding: str | None = None,
) -> types.GenerateContentConfig:
    tools = _build_grounding_tools(grounding)
    return types.GenerateContentConfig(
        response_modalities=["IMAGE", "TEXT"],
        image_config=build_image_config(aspect_ratio, image_size),
        tools=tools,
    )


def _extract_image(response: types.GenerateContentResponse, output: Path) -> None:
    candidate = response.candidates[0] if response.candidates else None
    content = candidate.content if candidate else None
    parts = content.parts if content else None

    if not parts:
        print("Error: empty response from API.", file=sys.stderr)
        sys.exit(1)

    for part in parts:
        if part.inline_data is not None:
            image_bytes = part.inline_data.data
            if image_bytes is None:
                continue
            if isinstance(image_bytes, str):
                image_bytes = base64.b64decode(image_bytes)
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_bytes(image_bytes)
            print(f"Image saved to {output}")
            return

    text_parts = [p.text for p in parts if p.text]
    if text_parts:
        print("\n".join(text_parts), file=sys.stderr)
    else:
        print("Error: no image in response.", file=sys.stderr)
    sys.exit(1)


def generate_image(
    prompt: str,
    base_url: str,
    model_name: str,
    api_key: str,
    output: Path,
    aspect_ratio: str | None = None,
    image_size: str | None = None,
    grounding: str | None = None,
) -> None:
    client = genai.Client(
        http_options=types.HttpOptions(base_url=base_url),
        api_key=api_key,
    )

    response = client.models.generate_content(
        model=model_name,
        contents=prompt,
        config=build_config(aspect_ratio, image_size, grounding),
    )

    _extract_image(response, output)


def edit_image(
    prompt: str,
    images: list[Path],
    base_url: str,
    model_name: str,
    api_key: str,
    output: Path,
    aspect_ratio: str | None = None,
    image_size: str | None = None,
    grounding: str | None = None,
) -> None:
    client = genai.Client(
        http_options=types.HttpOptions(base_url=base_url),
        api_key=api_key,
    )

    pil_images = [Image.open(img_path) for img_path in images]

    contents: list[
        str | Image.Image | types.File | types.FileDict | types.Part | types.PartDict
    ] = [
        prompt,
        *pil_images,
    ]
    response = client.models.generate_content(
        model=model_name,
        contents=contents,
        config=build_config(aspect_ratio, image_size, grounding),
    )

    _extract_image(response, output)
