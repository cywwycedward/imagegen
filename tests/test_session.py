from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from imagegen.session import create_session, list_sessions, load_session, save_turn


@pytest.fixture()
def sessions_dir(tmp_path: Path) -> Path:
    """Patch user_config_dir so sessions are stored under tmp_path."""
    config_dir = tmp_path / "config"
    with patch("imagegen.session.user_config_dir", return_value=config_dir):
        yield config_dir


class TestCreateSession:
    def test_creates_directory_and_metadata(self, sessions_dir: Path) -> None:
        session_id, session_dir = create_session("prov/model")

        assert len(session_id) == 12
        assert session_dir.is_dir()

        meta_path = session_dir / "metadata.json"
        assert meta_path.is_file()

        metadata = json.loads(meta_path.read_text())
        assert metadata["session_id"] == session_id
        assert metadata["model_spec"] == "prov/model"
        assert metadata["turns"] == []
        assert "created_at" in metadata

    def test_unique_ids(self, sessions_dir: Path) -> None:
        id1, _ = create_session("prov/model")
        id2, _ = create_session("prov/model")
        assert id1 != id2


class TestLoadSession:
    def test_load_existing(self, sessions_dir: Path) -> None:
        session_id, _ = create_session("prov/model")
        sess_dir, metadata = load_session(session_id)

        assert sess_dir.is_dir()
        assert metadata["session_id"] == session_id

    def test_load_nonexistent_exits(self, sessions_dir: Path) -> None:
        with pytest.raises(SystemExit):
            load_session("nonexistent-id")


class TestSaveTurn:
    def test_appends_turn(self, sessions_dir: Path) -> None:
        session_id, session_dir = create_session("prov/model")

        save_turn(session_dir, 0, "draw a cat", Path("turn_000.png"))
        save_turn(session_dir, 1, "make it blue", Path("turn_001.png"), ["ref.png"])

        metadata = json.loads((session_dir / "metadata.json").read_text())
        assert len(metadata["turns"]) == 2
        assert metadata["turns"][0]["prompt"] == "draw a cat"
        assert metadata["turns"][0]["turn"] == 0
        assert metadata["turns"][1]["input_images"] == ["ref.png"]

    def test_none_image_path(self, sessions_dir: Path) -> None:
        session_id, session_dir = create_session("prov/model")
        save_turn(session_dir, 0, "hello", None)

        metadata = json.loads((session_dir / "metadata.json").read_text())
        assert metadata["turns"][0]["output_image"] is None


class TestListSessions:
    def test_empty_when_no_sessions(self, sessions_dir: Path) -> None:
        assert list_sessions() == []

    def test_lists_created_sessions(self, sessions_dir: Path) -> None:
        create_session("prov/model-a")
        create_session("prov/model-b")

        sessions = list_sessions()
        assert len(sessions) == 2
        specs = {s["model_spec"] for s in sessions}
        assert specs == {"prov/model-a", "prov/model-b"}
