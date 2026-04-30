from __future__ import annotations

import json
from dataclasses import is_dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict


PROJECT_ROOT = Path(__file__).resolve().parents[2]


class RepoWriterError(Exception):
    """Raised when artifact writing fails."""


def ensure_parent_dir(file_path: Path) -> None:
    file_path.parent.mkdir(parents=True, exist_ok=True)


def _normalize_data(data: Any) -> Any:
    if is_dataclass(data):
        if hasattr(data, "to_dict"):
            return data.to_dict()
        raise RepoWriterError("Dataclass object is missing a to_dict() method.")

    if isinstance(data, dict):
        return data

    raise RepoWriterError("Unsupported data type for serialization.")


def write_json(relative_path: str, data: Any) -> Path:
    file_path = PROJECT_ROOT / relative_path
    ensure_parent_dir(file_path)

    normalized = _normalize_data(data)
    file_path.write_text(
        json.dumps(normalized, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return file_path


def write_markdown(relative_path: str, content: str) -> Path:
    if not isinstance(content, str):
        raise RepoWriterError("Markdown content must be a string.")

    file_path = PROJECT_ROOT / relative_path
    ensure_parent_dir(file_path)
    file_path.write_text(content.strip() + "\n", encoding="utf-8")
    return file_path


def append_jsonl(relative_path: str, data: Dict[str, Any]) -> Path:
    if not isinstance(data, dict):
        raise RepoWriterError("JSONL append data must be a dictionary.")

    file_path = PROJECT_ROOT / relative_path
    ensure_parent_dir(file_path)

    with file_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(data, ensure_ascii=False) + "\n")

    return file_path


def make_run_dir(run_id: str) -> Path:
    run_dir = PROJECT_ROOT / "runs" / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir


def timestamp_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_run_state_path(run_id: str) -> str:
    return f"runs/{run_id}/run_state.json"


def build_selected_topic_path(run_id: str) -> str:
    return f"runs/{run_id}/selected_topic.json"


def build_concept_note_run_path(run_id: str) -> str:
    return f"runs/{run_id}/concept_note.json"


def build_architect_note_run_path(run_id: str) -> str:
    return f"runs/{run_id}/architect_note.json"


def build_assessment_run_path(run_id: str) -> str:
    return f"runs/{run_id}/assessment.json"


def build_evaluation_run_path(run_id: str) -> str:
    return f"runs/{run_id}/evaluation.json"


def build_log_path(run_id: str) -> str:
    return f"runs/{run_id}/logs.txt"