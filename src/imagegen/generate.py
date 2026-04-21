from __future__ import annotations

import base64
import sys
from pathlib import Path

from google import genai
from google.genai import types


def generate_image(
    prompt: str,
    base_url: str,
    model_name: str,
    api_key: str,
    output: Path,
) -> None:
    client = genai.Client(
        http_options=types.HttpOptions(base_url=base_url),
        api_key=api_key,
    )

    response = client.models.generate_content(
        model=model_name,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_modalities=["IMAGE", "TEXT"],
        ),
    )

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
