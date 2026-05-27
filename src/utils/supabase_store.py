from __future__ import annotations

import json
import os
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv

try:
    import streamlit as st
except Exception:  # pragma: no cover
    st = None


PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")


class SupabaseStoreError(Exception):
    """Raised when Supabase persistence fails."""


def _secret(key: str, default: Any = None) -> Any:
    if st is not None:
        try:
            value = st.secrets.get(key, None)
            if value is not None:
                return value
        except Exception:
            pass
    return os.getenv(key, default)


def supabase_enabled() -> bool:
    value = _secret("SUPABASE_ENABLED", False)
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "1", "yes", "y"}


@lru_cache(maxsize=1)
def get_supabase_client():
    if not supabase_enabled():
        return None

    url = str(_secret("SUPABASE_URL", "")).strip().rstrip("/")
    key = str(_secret("SUPABASE_SERVICE_ROLE_KEY", "")).strip()

    if not url or not key:
        raise SupabaseStoreError(
            "Supabase is enabled, but SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY is missing."
        )

    try:
        from supabase import create_client
    except ImportError as exc:
        raise SupabaseStoreError(
            "supabase package is not installed. Add 'supabase' to requirements.txt."
        ) from exc

    return create_client(url, key)


def _json_safe(payload: Any) -> Any:
    if payload is None:
        return None
    if hasattr(payload, "to_dict"):
        return payload.to_dict()
    try:
        json.dumps(payload)
        return payload
    except TypeError:
        return json.loads(json.dumps(payload, default=str))


def upsert_run(
    run_id: str,
    topic_id: str,
    topic_title: str,
    phase: str,
    status: str,
    run_state: Dict[str, Any],
) -> None:
    client = get_supabase_client()
    if client is None:
        return

    row = {
        "run_id": run_id,
        "topic_id": topic_id,
        "topic_title": topic_title,
        "phase": phase,
        "status": status,
        "run_state": _json_safe(run_state),
    }
    client.table("mlos_runs").upsert(row, on_conflict="run_id").execute()


def upsert_artifact(
    run_id: str,
    artifact_type: str,
    topic_id: Optional[str] = None,
    payload: Any = None,
    text_payload: Optional[str] = None,
) -> None:
    client = get_supabase_client()
    if client is None:
        return

    row = {
        "run_id": run_id,
        "artifact_type": artifact_type,
        "topic_id": topic_id,
        "payload": _json_safe(payload),
        "text_payload": text_payload,
    }
    client.table("mlos_artifacts").upsert(row, on_conflict="run_id,artifact_type").execute()


def upsert_state(state_key: str, payload: Dict[str, Any]) -> None:
    client = get_supabase_client()
    if client is None:
        return

    row = {"state_key": state_key, "payload": _json_safe(payload)}
    client.table("mlos_state").upsert(row, on_conflict="state_key").execute()


def fetch_state(state_key: str) -> Optional[Dict[str, Any]]:
    client = get_supabase_client()
    if client is None:
        return None

    result = (
        client.table("mlos_state")
        .select("payload")
        .eq("state_key", state_key)
        .limit(1)
        .execute()
    )
    data = getattr(result, "data", None) or []
    if not data:
        return None
    payload = data[0].get("payload")
    return payload if isinstance(payload, dict) else None


def append_event(
    event_type: str,
    run_id: Optional[str] = None,
    topic_id: Optional[str] = None,
    payload: Optional[Dict[str, Any]] = None,
) -> None:
    client = get_supabase_client()
    if client is None:
        return

    row = {
        "run_id": run_id,
        "topic_id": topic_id,
        "event_type": event_type,
        "payload": _json_safe(payload or {}),
    }
    client.table("mlos_events").insert(row).execute()


def fetch_latest_runs(limit: int = 20) -> List[Dict[str, Any]]:
    client = get_supabase_client()
    if client is None:
        return []

    result = (
        client.table("mlos_runs")
        .select("*")
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    return getattr(result, "data", None) or []


def fetch_latest_run_by_phase(phase: str) -> Optional[Dict[str, Any]]:
    client = get_supabase_client()
    if client is None:
        return None

    result = (
        client.table("mlos_runs")
        .select("*")
        .eq("phase", phase)
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )
    data = getattr(result, "data", None) or []
    return data[0] if data else None


def fetch_run(run_id: str) -> Optional[Dict[str, Any]]:
    client = get_supabase_client()
    if client is None:
        return None

    result = client.table("mlos_runs").select("*").eq("run_id", run_id).limit(1).execute()
    data = getattr(result, "data", None) or []
    return data[0] if data else None


def fetch_run_artifacts(run_id: str) -> List[Dict[str, Any]]:
    client = get_supabase_client()
    if client is None:
        return []

    result = client.table("mlos_artifacts").select("*").eq("run_id", run_id).execute()
    return getattr(result, "data", None) or []


def fetch_topic_catalog_rows() -> List[Dict[str, Any]]:
    client = get_supabase_client()
    if client is None:
        return []

    result = (
        client.table("mlos_topic_catalog")
        .select("*")
        .eq("is_active", True)
        .order("sequence_no", desc=False)
        .execute()
    )
    return getattr(result, "data", None) or []


def upsert_learner_progress_rows(rows: List[Dict[str, Any]]) -> None:
    client = get_supabase_client()
    if client is None or not rows:
        return
    client.table("mlos_learner_progress").upsert(rows, on_conflict="topic_id").execute()


def fetch_learner_progress_rows() -> List[Dict[str, Any]]:
    client = get_supabase_client()
    if client is None:
        return []
    result = client.table("mlos_learner_progress").select("*").execute()
    return getattr(result, "data", None) or []

def fetch_topic_resources(topic_id: str) -> List[Dict[str, Any]]:
    """Return optional curated learning resources for a topic.

    This deliberately fails closed while Patch 039 code deploys before its
    additive SQL migration. Lessons remain usable even when the resource table
    has not been created yet or is temporarily unavailable.
    """
    client = get_supabase_client()
    if client is None or not str(topic_id or "").strip():
        return []
    try:
        result = (
            client.table("mlos_topic_resources")
            .select("resource_id,topic_id,resource_type,title,provider,url,purpose,estimated_minutes,is_primary,is_optional,sequence_order")
            .eq("topic_id", topic_id)
            .eq("is_active", True)
            .order("sequence_order", desc=False)
            .execute()
        )
        return getattr(result, "data", None) or []
    except Exception:
        return []

