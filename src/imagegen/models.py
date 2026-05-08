from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ResolvedModel:
    """Result of resolving a 'provider/model' spec against provider.json."""

    backend: str
    base_url: str
    model_name: str
    display_name: str
    api_key: str
    options: dict[str, list[str]]
