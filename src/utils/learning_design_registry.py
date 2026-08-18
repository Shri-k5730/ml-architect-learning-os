from __future__ import annotations

"""Single source of truth for runtime learning designs.

Priority:
1. V4 locally authored agentic lessons. These deliberately override older
   Supabase rows so a stale database design cannot reintroduce giveaway MCQs or
   hidden grading criteria.
2. Active Supabase design for non-agentic topics.
3. Bundled deterministic fallback.

All runtime components should resolve through this module instead of choosing
their own content source.
"""

from typing import Any, Dict, Optional

from src.blueprints.agentic_ai import get_agentic_learning_design
from src.blueprints.learning_design import get_bundled_learning_design
from src.utils.supabase_store import fetch_topic_learning_design
from src.utils.v23_tutor_quality import enhance_learning_design


def resolve_learning_design(topic_id: str) -> Optional[Dict[str, Any]]:
    tid = str(topic_id or "").strip()
    if not tid:
        return None

    authored_agentic = get_agentic_learning_design(tid)
    if authored_agentic is not None:
        return authored_agentic

    supabase_design = fetch_topic_learning_design(tid)
    if supabase_design is not None:
        return enhance_learning_design(supabase_design)

    # Bundled resolver already applies its deploy-safe enrichment once.
    return get_bundled_learning_design(tid)
