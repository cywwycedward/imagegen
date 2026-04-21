from __future__ import annotations

import base64
import sys
from pathlib import Path

from google import genai
from google.genai import types
from PIL import Image
from rich.console import Console

from imagegen.generate import build_config, build_image_config
from imagegen.session import create_session, load_session, save_turn


SLASH_HELP = """\
Commands:
  /image <path>    Attach image(s) to next message (space-separated)
  /aspect <ratio>  Set aspect ratio for next turn (e.g. 16:9)
  /size <size>     Set image size for next turn (e.g. 2K)
  /session         Show current session ID
  /help            Show this help
  /quit            Exit chat"""


def _parse_input(raw: str) -> tuple[str, list[Path]]:
    """Parse user input, extracting /image directives and returning (text, images)."""
    lines = raw.strip().split("\n")
    text_parts: list[str] = []
    images: list[Path] = []

    for line in lines:
        stripped = line.strip()
        if stripped.lower().startswith("/image "):
            paths = stripped[7:].strip().split()
            for p in paths:
                img_path = Path(p).expanduser()
                if not img_path.is_file():
                    print(f"Warning: image not found: {img_path}", file=sys.stderr)
                else:
                    images.append(img_path)
        else:
            text_parts.append(line)

    return "\n".join(text_parts).strip(), images


def run_chat(
    base_url: str,
    model_name: str,
    api_key: str,
    output_dir: Path,
    aspect_ratio: str | None = None,
    image_size: str | None = None,
    grounding: str | None = None,
    session_id: str | None = None,
    model_spec: str = "",
) -> None:
    console = Console()

    client = genai.Client(
        http_options=types.HttpOptions(base_url=base_url),
        api_key=api_key,
    )

    config = build_config(aspect_ratio, image_size, grounding)
    chat = client.chats.create(model=model_name, config=config)

    if session_id:
        sess_dir, metadata = load_session(session_id)
        turn_index = len(metadata.get("turns", []))
        console.print(f"[dim]Resumed session: {session_id}[/dim]")
    else:
        session_id, sess_dir = create_session(model_spec)
        turn_index = 0
        console.print(f"[dim]New session: {session_id}[/dim]")

    output_dir.mkdir(parents=True, exist_ok=True)

    console.print(f"[dim]Images saved to: {output_dir}[/dim]")
    console.print("[dim]Type /help for commands, /quit to exit.[/dim]\n")

    turn_aspect: str | None = None
    turn_size: str | None = None

    while True:
        try:
            user_input = console.input("[bold cyan]> [/bold cyan]")
        except (EOFError, KeyboardInterrupt):
            console.print("\n[dim]Goodbye.[/dim]")
            break

        stripped = user_input.strip()
        if not stripped:
            continue

        if stripped.lower() == "/quit":
            console.print("[dim]Goodbye.[/dim]")
            break

        if stripped.lower() == "/help":
            console.print(SLASH_HELP)
            continue

        if stripped.lower() == "/session":
            console.print(f"[dim]Session: {session_id}[/dim]")
            continue

        if stripped.lower().startswith("/aspect "):
            turn_aspect = stripped[8:].strip()
            console.print(f"[dim]Next turn aspect ratio: {turn_aspect}[/dim]")
            continue

        if stripped.lower().startswith("/size "):
            turn_size = stripped[6:].strip()
            console.print(f"[dim]Next turn image size: {turn_size}[/dim]")
            continue

        prompt_text, input_images = _parse_input(stripped)

        contents: list[str | Image.Image] = []
        if prompt_text:
            contents.append(prompt_text)
        for img_path in input_images:
            contents.append(Image.open(img_path))

        if not contents:
            continue

        turn_config: types.GenerateContentConfig | None = None
        image_cfg = build_image_config(turn_aspect, turn_size)
        if image_cfg is not None:
            turn_config = types.GenerateContentConfig(image_config=image_cfg)

        try:
            with console.status("[bold yellow]Generating...[/bold yellow]"):
                if turn_config is not None:
                    response = chat.send_message(contents, config=turn_config)
                else:
                    response = chat.send_message(contents)
        except Exception as exc:
            console.print(f"[red]Error: {exc}[/red]")
            continue

        turn_aspect = None
        turn_size = None

        candidate = response.candidates[0] if response.candidates else None
        content = candidate.content if candidate else None
        parts = content.parts if content else None

        if not parts:
            console.print("[yellow]Empty response.[/yellow]")
            continue

        image_path: Path | None = None
        for part in parts:
            if part.text:
                console.print(part.text)
            if part.inline_data is not None and part.inline_data.data is not None:
                image_bytes = part.inline_data.data
                if isinstance(image_bytes, str):
                    image_bytes = base64.b64decode(image_bytes)
                image_path = output_dir / f"turn_{turn_index:03d}.png"
                image_path.write_bytes(image_bytes)
                console.print(f"[green]Image saved: {image_path}[/green]")

        save_turn(
            sess_dir,
            turn_index,
            prompt_text,
            image_path,
            input_images=[str(p) for p in input_images] if input_images else None,
        )
        turn_index += 1
