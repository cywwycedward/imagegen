from __future__ import annotations

import json
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from imagegen.provider import user_config_dir


SESSIONS_DIR_NAME = "sessions"


def _sessions_dir() -> Path:
    return user_config_dir() / SESSIONS_DIR_NAME


def create_session(model_spec: str) -> tuple[str, Path]:
    """Create a new session directory and metadata file. Returns (session_id, session_dir)."""
    session_id = uuid.uuid4().hex[:12]
    session_dir = _sessions_dir() / session_id
    session_dir.mkdir(parents=True, exist_ok=True)

    metadata: dict[str, Any] = {
        "session_id": session_id,
        "model_spec": model_spec,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "turns": [],
    }
    (session_dir / "metadata.json").write_text(json.dumps(metadata, indent=2))

    return session_id, session_dir


def load_session(session_id: str) -> tuple[Path, dict[str, Any]]:

    session_dir = _sessions_dir() / session_id
    meta_path = session_dir / "metadata.json"
    if not meta_path.is_file():
        print(
            f"Error: session '{session_id}' not found.",
            file=sys.stderr,
        )
        sys.exit(1)

    with meta_path.open() as f:
        metadata: dict[str, Any] = json.load(f)

    return session_dir, metadata


def save_turn(
    session_dir: Path,
    turn_index: int,
    prompt: str,
    image_path: Path | None,
    input_images: list[str] | None = None,
) -> None:

    meta_path = session_dir / "metadata.json"
    with meta_path.open() as f:
        metadata: dict[str, Any] = json.load(f)

    turn_record: dict[str, Any] = {
        "turn": turn_index,
        "prompt": prompt,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "output_image": str(image_path) if image_path else None,
    }
    if input_images:
        turn_record["input_images"] = input_images

    metadata["turns"].append(turn_record)
    meta_path.write_text(json.dumps(metadata, indent=2))


def list_sessions() -> list[dict[str, Any]]:

    sessions_dir = _sessions_dir()
    if not sessions_dir.is_dir():
        return []

    result: list[dict[str, Any]] = []
    for entry in sorted(sessions_dir.iterdir()):
        meta_path = entry / "metadata.json"
        if meta_path.is_file():
            with meta_path.open() as f:
                metadata: dict[str, Any] = json.load(f)
            result.append(metadata)
    return result
