from __future__ import annotations

from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

from imagegen.generate import generate_image
from imagegen.provider import ensure_user_config, load_providers, resolve_model


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


@main.command()
@click.argument("prompt")
@click.argument("model_spec")
@click.argument("output")
def generate(prompt: str, model_spec: str, output: str) -> None:
    base_url, model_name, _display_name, api_key = resolve_model(model_spec)
    generate_image(
        prompt=prompt,
        base_url=base_url,
        model_name=model_name,
        api_key=api_key,
        output=Path(output),
    )
