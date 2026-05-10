from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

PROJECT_ROOT = Path(__file__).resolve().parents[2]
TOPIC_CATALOG_PATH = PROJECT_ROOT / "topics" / "topic_catalog.json"
UNLOCK_RULES_PATH = PROJECT_ROOT / "topics" / "topic_unlock_rules.json"

TOPIC_FIELDS = {
    "topic_id",
    "title",
    "domain",
    "difficulty",
    "prerequisites",
    "architect_relevance",
    "tags",
}


def _safe_list(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value]
    if isinstance(value, str):
        value = value.strip()
        if not value:
            return []
        try:
            parsed = json.loads(value)
            if isinstance(parsed, list):
                return [str(item) for item in parsed]
        except Exception:
            return [value]
    return []


def _read_local_topic_catalog() -> List[Dict[str, Any]]:
    if not TOPIC_CATALOG_PATH.exists():
        return []
    data = json.loads(TOPIC_CATALOG_PATH.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        return []
    return [_normalize_topic_dict(item) for item in data if isinstance(item, dict)]


def _normalize_topic_dict(item: Dict[str, Any]) -> Dict[str, Any]:
    topic_id = str(item.get("topic_id", "")).strip()
    title = str(item.get("title", "")).strip()
    domain = str(item.get("domain", "")).strip()

    try:
        difficulty = int(item.get("difficulty", 1) or 1)
    except Exception:
        difficulty = 1

    return {
        "topic_id": topic_id,
        "title": title,
        "domain": domain,
        "difficulty": difficulty,
        "prerequisites": _safe_list(item.get("prerequisites")),
        "architect_relevance": _safe_list(item.get("architect_relevance")),
        "tags": _safe_list(item.get("tags")),
    }


def _catalog_row_to_topic(row: Dict[str, Any]) -> Dict[str, Any]:
    # New Supabase rows store prerequisites as JSONB. Older/minimal rows may only
    # have unlock_after, so we support both.
    prerequisites = _safe_list(row.get("prerequisites"))
    if not prerequisites:
        unlock_after = str(row.get("unlock_after") or "").strip()
        if unlock_after:
            prerequisites = [unlock_after]

    return _normalize_topic_dict(
        {
            "topic_id": row.get("topic_id"),
            "title": row.get("title"),
            "domain": row.get("domain"),
            "difficulty": row.get("difficulty"),
            "prerequisites": prerequisites,
            "architect_relevance": row.get("architect_relevance") or [],
            "tags": row.get("tags") or [],
        }
    )


def _topic_to_catalog_row(topic: Dict[str, Any], sequence_no: int) -> Dict[str, Any]:
    topic = _normalize_topic_dict(topic)
    prerequisites = topic.get("prerequisites", [])
    topic_id = topic["topic_id"]
    item_type = "checkpoint" if topic_id.startswith("checkpoint_") else "lesson"
    module_id = _infer_module_id(topic_id, sequence_no, item_type)

    return {
        "topic_id": topic_id,
        "title": topic["title"],
        "domain": topic["domain"],
        "module_id": module_id,
        "sequence_no": sequence_no,
        "item_type": item_type,
        "difficulty": int(topic.get("difficulty", 1) or 1),
        "prerequisites": prerequisites,
        "unlock_after": prerequisites[-1] if prerequisites else None,
        "architect_relevance": topic.get("architect_relevance", []),
        "tags": topic.get("tags", []),
        "is_active": True,
    }


def _infer_module_id(topic_id: str, sequence_no: int, item_type: str) -> str:
    if item_type == "checkpoint":
        return "module_001_checkpoint"
    if topic_id.startswith("mlf_"):
        try:
            number = int(topic_id.split("_")[1])
        except Exception:
            number = sequence_no
        if number <= 10:
            return "module_001_ml_foundations"
        if number <= 20:
            return "module_002_advanced_ml"
    return "module_999_uncategorized"


def _fetch_supabase_topic_catalog() -> List[Dict[str, Any]]:
    try:
        from src.utils.supabase_store import get_supabase_client, supabase_enabled

        if not supabase_enabled():
            return []
        client = get_supabase_client()
        if client is None:
            return []
        result = (
            client.table("mlos_topic_catalog")
            .select(
                "topic_id,title,domain,module_id,sequence_no,item_type,difficulty,"
                "prerequisites,unlock_after,architect_relevance,tags,is_active"
            )
            .eq("is_active", True)
            .order("sequence_no", desc=False)
            .execute()
        )
        rows = getattr(result, "data", None) or []
        return [_catalog_row_to_topic(row) for row in rows if isinstance(row, dict)]
    except Exception:
        # Table may not exist yet. Fallback is intentional so the app still boots.
        return []


def load_topic_catalog_dicts(prefer_supabase: bool = True) -> List[Dict[str, Any]]:
    if prefer_supabase:
        cloud_rows = _fetch_supabase_topic_catalog()
        if cloud_rows:
            return cloud_rows
    return _read_local_topic_catalog()


def load_topic_catalog_source() -> Tuple[str, int]:
    cloud_rows = _fetch_supabase_topic_catalog()
    if cloud_rows:
        return "supabase:mlos_topic_catalog", len(cloud_rows)
    local_rows = _read_local_topic_catalog()
    return "local:topics/topic_catalog.json", len(local_rows)


def build_catalog_rows_for_supabase() -> List[Dict[str, Any]]:
    topics = _read_local_topic_catalog()
    return [_topic_to_catalog_row(topic, idx + 1) for idx, topic in enumerate(topics)]


def seed_supabase_catalog_from_local_if_empty() -> Dict[str, Any]:
    """Seed mlos_topic_catalog from local JSON only if the table exists and is empty.

    This does not create tables. Run supabase/sql/006_curriculum_catalog.sql first.
    The function is safe to call on every startup.
    """
    summary = {
        "enabled": False,
        "table_available": False,
        "seeded": False,
        "existing_count": 0,
        "local_count": 0,
        "error": None,
    }
    try:
        from src.utils.supabase_store import get_supabase_client, supabase_enabled

        summary["enabled"] = supabase_enabled()
        if not supabase_enabled():
            return summary
        client = get_supabase_client()
        if client is None:
            return summary

        probe = client.table("mlos_topic_catalog").select("topic_id", count="exact").limit(1).execute()
        summary["table_available"] = True
        existing = getattr(probe, "count", None)
        if existing is None:
            existing = len(getattr(probe, "data", None) or [])
        summary["existing_count"] = int(existing or 0)
        if summary["existing_count"] > 0:
            return summary

        rows = build_catalog_rows_for_supabase()
        summary["local_count"] = len(rows)
        if rows:
            client.table("mlos_topic_catalog").upsert(rows, on_conflict="topic_id").execute()
            summary["seeded"] = True
        return summary
    except Exception as exc:
        summary["error"] = str(exc)
        return summary
