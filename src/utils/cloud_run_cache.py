from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from src.utils.supabase_store import fetch_run_artifacts, get_supabase_client, supabase_enabled


PROJECT_ROOT = Path(__file__).resolve().parents[2]
RUNS_DIR = PROJECT_ROOT / "runs"
ASSESSMENT_ANSWERS_DIR = PROJECT_ROOT / "assessments" / "answers"


ARTIFACT_LOCAL_FILES: Dict[str, str] = {
    "selected_topic": "selected_topic.json",
    "concept_note": "concept_note.json",
    "architect_note": "architect_note.json",
    "assessment": "assessment.json",
    "evaluation": "evaluation.json",
    "answer_coaching": "answer_coaching.json",
    "practice_exercise": "practice_exercise.json",
    "practice_result": "practice_result.json",
    "practice_coaching": "practice_coaching.json",
    "draft_verification": "draft_verification.json",
    "lesson_blueprint": "lesson_blueprint.json",
    "capstone_deliverables": "capstone_deliverables.json",
}


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def _payload(row: Dict[str, Any]) -> Any:
    if row.get("payload") is not None:
        return row.get("payload")
    if row.get("text_payload"):
        try:
            return json.loads(row.get("text_payload") or "")
        except Exception:
            return row.get("text_payload")
    return None


def _artifact_map(rows: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for row in rows or []:
        artifact_type = str(row.get("artifact_type") or "").strip()
        if not artifact_type:
            continue
        out[artifact_type] = _payload(row)
    return out


def _default_run_state(run_row: Dict[str, Any], artifacts: Dict[str, Any]) -> Dict[str, Any]:
    run_id = str(run_row.get("run_id") or "").strip()
    topic_id = str(run_row.get("topic_id") or "").strip()
    topic_title = str(run_row.get("topic_title") or topic_id)
    phase = str(run_row.get("phase") or "awaiting_user_answers")
    status = str(run_row.get("status") or "in_progress")
    answer_payload = artifacts.get("answers") or artifacts.get("answer_template") or {}
    practice_exercise = artifacts.get("practice_exercise")
    practice_submission = artifacts.get("practice_submission") or artifacts.get("practice_submission_template")

    state = {
        "run_id": run_id,
        "topic_id": topic_id,
        "topic_name": topic_title,
        "phase": phase,
        "status": status,
        "prerequisites": [],
        "artifacts": {
            "concept_note": f"runs/{run_id}/concept_note.json" if artifacts.get("concept_note") else None,
            "architect_note": f"runs/{run_id}/architect_note.json" if artifacts.get("architect_note") else None,
            "assessment": f"runs/{run_id}/assessment.json" if artifacts.get("assessment") else None,
            "answers": f"assessments/answers/{run_id}_answers.json" if answer_payload else None,
            "evaluation": f"runs/{run_id}/evaluation.json" if artifacts.get("evaluation") else None,
            "practice_exercise": f"runs/{run_id}/practice_exercise.json" if practice_exercise else None,
            "practice_submission": f"assessments/answers/{run_id}_practice_submission.json" if practice_submission else None,
            "practice_result": f"runs/{run_id}/practice_result.json" if artifacts.get("practice_result") else None,
            "practice_coaching": f"runs/{run_id}/practice_coaching.json" if artifacts.get("practice_coaching") else None,
            "capstone_deliverables": f"runs/{run_id}/capstone_deliverables.json" if artifacts.get("capstone_deliverables") else None,
        },
        "scores": {},
        "next_action": "await_user_answers" if phase == "awaiting_user_answers" else "next_topic",
    }
    if artifacts.get("evaluation") and isinstance(artifacts["evaluation"], dict):
        state["scores"] = artifacts["evaluation"].get("scores") or {}
    return state


def _normalize_run_state(run_row: Dict[str, Any], artifacts: Dict[str, Any]) -> Dict[str, Any]:
    state = run_row.get("run_state")
    if not isinstance(state, dict):
        state = _default_run_state(run_row, artifacts)

    run_id = str(run_row.get("run_id") or state.get("run_id") or "").strip()
    topic_id = str(run_row.get("topic_id") or state.get("topic_id") or "").strip()
    state.setdefault("run_id", run_id)
    state.setdefault("topic_id", topic_id)
    state.setdefault("topic_name", run_row.get("topic_title") or topic_id)
    state["phase"] = str(run_row.get("phase") or state.get("phase") or "awaiting_user_answers")
    state["status"] = str(run_row.get("status") or state.get("status") or "in_progress")
    state.setdefault("prerequisites", [])
    state.setdefault("scores", {})
    if not state.get("next_action"):
        state["next_action"] = "await_user_answers" if state["phase"] == "awaiting_user_answers" else "next_topic"

    local_defaults = _default_run_state(run_row, artifacts).get("artifacts", {})
    state_artifacts = state.get("artifacts") if isinstance(state.get("artifacts"), dict) else {}
    for key, value in local_defaults.items():
        if value and not state_artifacts.get(key):
            state_artifacts[key] = value
    state["artifacts"] = state_artifacts
    return state


def materialize_run_from_supabase(run_row: Dict[str, Any]) -> Optional[Path]:
    """Recreate the local run folder from Supabase artifacts.

    Streamlit Cloud local storage is not durable. This function lets the app and
    evaluator rebuild the local files they still expect, using Supabase as the
    system of record.
    """
    run_id = str(run_row.get("run_id") or "").strip()
    if not run_id:
        return None

    try:
        artifact_rows = fetch_run_artifacts(run_id)
    except Exception:
        artifact_rows = []
    artifacts = _artifact_map(artifact_rows)
    state = _normalize_run_state(run_row, artifacts)

    run_dir = RUNS_DIR / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    for artifact_type, filename in ARTIFACT_LOCAL_FILES.items():
        if artifact_type in artifacts and artifacts[artifact_type] is not None:
            _write_json(run_dir / filename, artifacts[artifact_type])

    answer_payload = artifacts.get("answers") or artifacts.get("answer_template")
    answer_rel = ((state.get("artifacts") or {}).get("answers")) or f"assessments/answers/{run_id}_answers.json"
    if answer_payload is not None:
        _write_json(PROJECT_ROOT / answer_rel, answer_payload)
        state.setdefault("artifacts", {})["answers"] = answer_rel

    practice_payload = artifacts.get("practice_submission") or artifacts.get("practice_submission_template")
    practice_rel = ((state.get("artifacts") or {}).get("practice_submission")) or f"assessments/answers/{run_id}_practice_submission.json"
    if practice_payload is not None:
        _write_json(PROJECT_ROOT / practice_rel, practice_payload)
        state.setdefault("artifacts", {})["practice_submission"] = practice_rel

    _write_json(run_dir / "run_state.json", state)
    log_path = run_dir / "logs.txt"
    if not log_path.exists():
        log_path.write_text("[cloud-cache] materialized from Supabase\n", encoding="utf-8")
    return run_dir


def _topic_status(progress_rows: List[Dict[str, str]], topic_id: str) -> str:
    for row in progress_rows or []:
        if str(row.get("topic_id") or "") == topic_id:
            return str(row.get("status") or "").strip().lower()
    return ""


def fetch_latest_run_rows_by_phase(phase: str, limit: int = 10) -> List[Dict[str, Any]]:
    if not supabase_enabled():
        return []
    client = get_supabase_client()
    if client is None:
        return []
    result = (
        client.table("mlos_runs")
        .select("*")
        .eq("phase", phase)
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    return getattr(result, "data", None) or []


def fetch_latest_run_row_by_phase(phase: str, limit: int = 10) -> Optional[Dict[str, Any]]:
    rows = fetch_latest_run_rows_by_phase(phase, limit=limit)
    return rows[0] if rows else None


def _is_redo_run(row: Dict[str, Any]) -> bool:
    run_state = row.get("run_state") if isinstance(row.get("run_state"), dict) else {}
    return run_state.get("redo_mode") is True or str(run_state.get("selection_mode") or "") == "retry"


def sync_active_run_from_supabase(progress_rows: Optional[List[Dict[str, str]]] = None) -> Optional[Path]:
    if not supabase_enabled():
        return None

    # There can be stale awaiting runs in Supabase from earlier bugs. Iterate
    # recent candidates and materialize the first legitimate active run instead
    # of letting one bad completed-topic run hide a newer valid lesson.
    for row in fetch_latest_run_rows_by_phase("awaiting_user_answers", limit=10):
        topic_id = str(row.get("topic_id") or "").strip()
        status = str(row.get("status") or "").strip().lower()
        if status not in {"in_progress", "awaiting_user_answers", "started"}:
            continue
        if progress_rows is not None and _topic_status(progress_rows, topic_id) == "completed" and not _is_redo_run(row):
            continue
        return materialize_run_from_supabase(row)
    return None


def sync_latest_evaluation_from_supabase() -> Optional[Path]:
    if not supabase_enabled():
        return None
    row = fetch_latest_run_row_by_phase("evaluation_complete", limit=10)
    if not row:
        return None
    return materialize_run_from_supabase(row)
