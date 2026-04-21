from __future__ import annotations

from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

from imagegen.chat import run_chat
from imagegen.generate import edit_image, generate_image
from imagegen.provider import (
    ensure_user_config,
    load_providers,
    resolve_model,
    validate_option,
)
from imagegen.session import list_sessions


@click.group()
def main() -> None:
    pass


@main.group()
def provider() -> None:
    pass


@provider.command(name="init")
def provider_init() -> None:
    path = ensure_user_config()
    Console().print(f"[green]Provider config ready at:[/green] {path}")


@provider.command(name="list")
@click.option("--model", is_flag=True, help="Show models with their providers")
def provider_list(model: bool) -> None:
    console = Console()
    providers = load_providers()

    if not providers:
        console.print("[yellow]No providers configured in provider.json[/yellow]")
        return

    if model:
        table = Table(show_header=True)
        table.add_column("Model", style="cyan")
        table.add_column("Provider", style="green")
        for p in providers:
            for model_key, model_info in p.get("models", {}).items():
                table.add_row(model_info.get("name", model_key), p["name"])
        console.print(table)
    else:
        table = Table(show_header=True)
        table.add_column("Provider", style="green")
        for p in providers:
            table.add_row(p["name"])
        console.print(table)


def _validate_generate_options(
    model_name: str,
    options: dict[str, list[str]],
    aspect_ratio: str | None,
    image_size: str | None,
    grounding: str | None,
) -> None:
    if aspect_ratio is not None:
        validate_option(
            aspect_ratio, options["aspect_ratio"], "--aspect-ratio", model_name
        )
    if image_size is not None:
        validate_option(image_size, options["image_size"], "--image-size", model_name)
    if grounding is not None:
        validate_option(grounding, options["grounding"], "--grounding", model_name)


@main.command()
@click.argument("prompt")
@click.argument("model_spec")
@click.argument("output")
@click.option(
    "--aspect-ratio", default=None, help="Image aspect ratio (e.g. 16:9, 1:1)"
)
@click.option("--image-size", default=None, help="Image resolution (e.g. 1K, 2K, 4K)")
@click.option(
    "--grounding",
    type=click.Choice(["google-search", "image-search"]),
    default=None,
    help="Enable grounding (google-search or image-search)",
)
def generate(
    prompt: str,
    model_spec: str,
    output: str,
    aspect_ratio: str | None,
    image_size: str | None,
    grounding: str | None,
) -> None:
    base_url, model_name, _display_name, api_key, options = resolve_model(model_spec)
    _validate_generate_options(model_name, options, aspect_ratio, image_size, grounding)

    generate_image(
        prompt=prompt,
        base_url=base_url,
        model_name=model_name,
        api_key=api_key,
        output=Path(output),
        aspect_ratio=aspect_ratio,
        image_size=image_size,
        grounding=grounding,
    )


@main.command()
@click.argument("prompt")
@click.argument("model_spec")
@click.argument("output")
@click.option(
    "--image",
    "images",
    multiple=True,
    required=True,
    type=click.Path(exists=True),
    help="Reference image path (can be specified multiple times)",
)
@click.option(
    "--aspect-ratio", default=None, help="Image aspect ratio (e.g. 16:9, 1:1)"
)
@click.option("--image-size", default=None, help="Image resolution (e.g. 1K, 2K, 4K)")
@click.option(
    "--grounding",
    type=click.Choice(["google-search", "image-search"]),
    default=None,
    help="Enable grounding (google-search or image-search)",
)
def edit(
    prompt: str,
    model_spec: str,
    output: str,
    images: tuple[str, ...],
    aspect_ratio: str | None,
    image_size: str | None,
    grounding: str | None,
) -> None:
    base_url, model_name, _display_name, api_key, options = resolve_model(model_spec)
    _validate_generate_options(model_name, options, aspect_ratio, image_size, grounding)

    edit_image(
        prompt=prompt,
        images=[Path(p) for p in images],
        base_url=base_url,
        model_name=model_name,
        api_key=api_key,
        output=Path(output),
        aspect_ratio=aspect_ratio,
        image_size=image_size,
        grounding=grounding,
    )


@main.command()
@click.argument("model_spec")
@click.option(
    "--output-dir",
    default=".",
    type=click.Path(),
    help="Directory to save generated images",
)
@click.option(
    "--session",
    "session_id",
    default=None,
    help="Resume an existing chat session by ID",
)
@click.option(
    "--aspect-ratio", default=None, help="Default aspect ratio for the session"
)
@click.option(
    "--image-size", default=None, help="Default image resolution for the session"
)
@click.option(
    "--grounding",
    type=click.Choice(["google-search", "image-search"]),
    default=None,
    help="Enable grounding for the session",
)
def chat(
    model_spec: str,
    output_dir: str,
    session_id: str | None,
    aspect_ratio: str | None,
    image_size: str | None,
    grounding: str | None,
) -> None:
    base_url, model_name, _display_name, api_key, options = resolve_model(model_spec)
    _validate_generate_options(model_name, options, aspect_ratio, image_size, grounding)

    run_chat(
        base_url=base_url,
        model_name=model_name,
        api_key=api_key,
        output_dir=Path(output_dir),
        aspect_ratio=aspect_ratio,
        image_size=image_size,
        grounding=grounding,
        session_id=session_id,
        model_spec=model_spec,
    )


@provider.command(name="sessions")
def provider_sessions() -> None:
    console = Console()
    sessions = list_sessions()

    if not sessions:
        console.print("[yellow]No chat sessions found.[/yellow]")
        return

    table = Table(show_header=True)
    table.add_column("Session ID", style="cyan")
    table.add_column("Model", style="green")
    table.add_column("Turns", style="yellow")
    table.add_column("Created", style="dim")
    for s in sessions:
        table.add_row(
            s.get("session_id", ""),
            s.get("model_spec", ""),
            str(len(s.get("turns", []))),
            s.get("created_at", ""),
        )
    console.print(table)
