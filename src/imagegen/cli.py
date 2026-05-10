from __future__ import annotations

import sys
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

from imagegen.backends import edit as backend_edit
from imagegen.backends import generate as backend_generate
from imagegen.chat import run_chat
from imagegen.provider import (
    ensure_user_config,
    get_model_options,
    load_providers,
    resolve_model,
    validate_backend_option,
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
@click.option(
    "--options",
    is_flag=True,
    help="Show supported options for each model (implies --model)",
)
def provider_list(model: bool, options: bool) -> None:
    console = Console()
    providers = load_providers()

    if not providers:
        console.print("[yellow]No providers configured in provider.json[/yellow]")
        return

    if options:
        genai_models = []
        openai_models = []
        for p in providers:
            backend = p.get("backend", "genai")
            for model_key, model_info in p.get("models", {}).items():
                opts = get_model_options(model_info, backend)
                entry = (model_key, p["name"], backend, opts)
                if backend == "openai":
                    openai_models.append(entry)
                else:
                    genai_models.append(entry)

        if genai_models:
            table = Table(show_header=True, title="GenAI Models")
            table.add_column("Model ID", style="cyan")
            table.add_column("Provider", style="green")
            table.add_column("Aspect Ratio", style="yellow")
            table.add_column("Image Size", style="yellow")
            table.add_column("Grounding", style="yellow")
            for model_key, pname, _, opts in genai_models:
                table.add_row(
                    model_key,
                    pname,
                    ", ".join(opts["aspect_ratio"]) or "-",
                    ", ".join(opts["image_size"]) or "-",
                    ", ".join(opts["grounding"]) or "-",
                )
            console.print(table)

        if openai_models:
            table = Table(show_header=True, title="OpenAI Models")
            table.add_column("Model ID", style="cyan")
            table.add_column("Provider", style="green")
            table.add_column("Size", style="yellow")
            table.add_column("Quality", style="yellow")
            table.add_column("Background", style="yellow")
            table.add_column("Style", style="yellow")
            for model_key, pname, _, opts in openai_models:
                table.add_row(
                    model_key,
                    pname,
                    ", ".join(opts["size"]) or "-",
                    ", ".join(opts["quality"]) or "-",
                    ", ".join(opts["background"]) or "-",
                    ", ".join(opts["style"]) or "-",
                )
            console.print(table)
    elif model:
        table = Table(show_header=True)
        table.add_column("Model ID", style="cyan")
        table.add_column("Model Name", style="yellow")
        table.add_column("Provider", style="green")
        table.add_column("Backend", style="blue")
        for p in providers:
            backend = p.get("backend", "genai")
            for model_key, model_info in p.get("models", {}).items():
                table.add_row(
                    model_key,
                    model_info.get("name", model_key),
                    p["name"],
                    backend,
                )
        console.print(table)
    else:
        table = Table(show_header=True)
        table.add_column("Provider", style="green")
        table.add_column("Backend", style="blue")
        for p in providers:
            table.add_row(p["name"], p.get("backend", "genai"))
        console.print(table)


def _validate_generate_options(
    model_name: str,
    backend: str,
    options: dict[str, list[str]],
    *,
    aspect_ratio: str | None,
    image_size: str | None,
    grounding: str | None,
    size: str | None,
    quality: str | None,
    background: str | None,
    style: str | None,
) -> None:
    validate_backend_option(aspect_ratio, "--aspect-ratio", backend, "genai")
    validate_backend_option(image_size, "--image-size", backend, "genai")
    validate_backend_option(grounding, "--grounding", backend, "genai")
    validate_backend_option(size, "--size", backend, "openai")
    validate_backend_option(quality, "--quality", backend, "openai")
    validate_backend_option(background, "--background", backend, "openai")
    validate_backend_option(style, "--style", backend, "openai")

    if aspect_ratio is not None:
        validate_option(
            aspect_ratio, options["aspect_ratio"], "--aspect-ratio", model_name
        )
    if image_size is not None:
        validate_option(image_size, options["image_size"], "--image-size", model_name)
    if grounding is not None:
        validate_option(grounding, options["grounding"], "--grounding", model_name)
    if size is not None:
        validate_option(size, options["size"], "--size", model_name)
    if quality is not None:
        validate_option(quality, options["quality"], "--quality", model_name)
    if background is not None:
        validate_option(background, options["background"], "--background", model_name)
    if style is not None:
        validate_option(style, options["style"], "--style", model_name)


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
@click.option(
    "--size",
    default=None,
    help="Image size (OpenAI: auto/1024x1024/1536x1024/1024x1536)",
)
@click.option(
    "--quality",
    default=None,
    help="Image quality (OpenAI: low/medium/high/auto)",
)
@click.option(
    "--background",
    default=None,
    help="Background (OpenAI: transparent/opaque/auto)",
)
@click.option(
    "--output-format",
    default=None,
    help="Output format (OpenAI: png/jpeg/webp)",
)
@click.option(
    "--output-compression",
    default=None,
    type=int,
    help="Compression 0-100 (OpenAI jpeg/webp only)",
)
@click.option(
    "--n",
    "num_images",
    default=None,
    type=int,
    help="Number of images to generate (OpenAI: 1-10)",
)
@click.option(
    "--style",
    default=None,
    help="Style (dall-e-3: vivid/natural)",
)
def generate(
    prompt: str,
    model_spec: str,
    output: str,
    aspect_ratio: str | None,
    image_size: str | None,
    grounding: str | None,
    size: str | None,
    quality: str | None,
    background: str | None,
    output_format: str | None,
    output_compression: int | None,
    num_images: int | None,
    style: str | None,
) -> None:
    model = resolve_model(model_spec)
    _validate_generate_options(
        model.model_name,
        model.backend,
        model.options,
        aspect_ratio=aspect_ratio,
        image_size=image_size,
        grounding=grounding,
        size=size,
        quality=quality,
        background=background,
        style=style,
    )

    backend_generate(
        backend=model.backend,
        prompt=prompt,
        base_url=model.base_url,
        model_name=model.model_name,
        api_key=model.api_key,
        output=Path(output),
        aspect_ratio=aspect_ratio,
        image_size=image_size,
        grounding=grounding,
        size=size,
        quality=quality,
        background=background,
        output_format=output_format,
        output_compression=output_compression,
        n=num_images,
        style=style,
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
@click.option(
    "--size",
    default=None,
    help="Image size (OpenAI: auto/1024x1024/1536x1024/1024x1536)",
)
@click.option(
    "--quality",
    default=None,
    help="Image quality (OpenAI: low/medium/high/auto)",
)
@click.option(
    "--background",
    default=None,
    help="Background (OpenAI: transparent/opaque/auto)",
)
@click.option(
    "--output-format",
    default=None,
    help="Output format (OpenAI: png/jpeg/webp)",
)
@click.option(
    "--output-compression",
    default=None,
    type=int,
    help="Compression 0-100 (OpenAI jpeg/webp only)",
)
@click.option(
    "--n",
    "num_images",
    default=None,
    type=int,
    help="Number of images to generate (OpenAI: 1-10)",
)
@click.option(
    "--mask",
    default=None,
    type=click.Path(exists=True),
    help="Mask image for editing (OpenAI)",
)
@click.option(
    "--input-fidelity",
    default=None,
    help="Input fidelity (OpenAI: high/low)",
)
def edit(
    prompt: str,
    model_spec: str,
    output: str,
    images: tuple[str, ...],
    aspect_ratio: str | None,
    image_size: str | None,
    grounding: str | None,
    size: str | None,
    quality: str | None,
    background: str | None,
    output_format: str | None,
    output_compression: int | None,
    num_images: int | None,
    mask: str | None,
    input_fidelity: str | None,
) -> None:
    model = resolve_model(model_spec)
    _validate_generate_options(
        model.model_name,
        model.backend,
        model.options,
        aspect_ratio=aspect_ratio,
        image_size=image_size,
        grounding=grounding,
        size=size,
        quality=quality,
        background=background,
        style=None,
    )

    backend_edit(
        backend=model.backend,
        prompt=prompt,
        images=[Path(p) for p in images],
        base_url=model.base_url,
        model_name=model.model_name,
        api_key=model.api_key,
        output=Path(output),
        aspect_ratio=aspect_ratio,
        image_size=image_size,
        grounding=grounding,
        size=size,
        quality=quality,
        background=background,
        output_format=output_format,
        output_compression=output_compression,
        n=num_images,
        mask=mask,
        input_fidelity=input_fidelity,
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
    model = resolve_model(model_spec)

    if model.backend != "genai":
        print(
            f"Error: chat is not supported for {model.backend} backend. "
            "Use 'imagegen generate' instead.",
            file=sys.stderr,
        )
        sys.exit(1)

    _validate_generate_options(
        model.model_name,
        model.backend,
        model.options,
        aspect_ratio=aspect_ratio,
        image_size=image_size,
        grounding=grounding,
        size=None,
        quality=None,
        background=None,
        style=None,
    )

    run_chat(
        base_url=model.base_url,
        model_name=model.model_name,
        api_key=model.api_key,
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
