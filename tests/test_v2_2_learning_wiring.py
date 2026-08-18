from src.utils.v2_progress_rebuilder import rebuild_v2_progress_state


def test_failed_redo_stays_active_and_locks_capstone_dl():
    catalog = [
        {"topic_id": "mlf_001", "title": "A", "domain": "ml", "difficulty": 1, "sequence_no": 1, "prerequisites": []},
        {"topic_id": "mlf_002", "title": "B", "domain": "ml", "difficulty": 1, "sequence_no": 2, "prerequisites": ["mlf_001"]},
        {"topic_id": "checkpoint_ml_architect_001", "title": "C", "domain": "ml", "difficulty": 3, "sequence_no": 3, "prerequisites": ["mlf_002"]},
        {"topic_id": "capstone_ml_architect_001", "title": "D", "domain": "ml", "difficulty": 4, "sequence_no": 4, "prerequisites": ["checkpoint_ml_architect_001"]},
        {"topic_id": "dl_001", "title": "E", "domain": "dl", "difficulty": 1, "sequence_no": 5, "prerequisites": ["capstone_ml_architect_001"]},
    ]
    progress = [
        {"topic_id": "mlf_001", "attempt_count": 2, "last_decision": "revise", "last_score_conceptual": 2, "last_score_practical": 2, "last_score_architect": 2, "last_score_communication": 2},
        {"topic_id": "mlf_002", "attempt_count": 1, "last_decision": "borderline", "last_score_conceptual": 3, "last_score_practical": 3, "last_score_architect": 3, "last_score_communication": 3},
        {"topic_id": "checkpoint_ml_architect_001", "attempt_count": 1, "last_decision": "pass", "last_score_conceptual": 4, "last_score_practical": 4, "last_score_architect": 4, "last_score_communication": 4},
        {"topic_id": "capstone_ml_architect_001", "attempt_count": 1, "last_decision": "pass", "last_score_conceptual": 4, "last_score_practical": 4, "last_score_architect": 4, "last_score_communication": 4},
    ]
    rows, active = rebuild_v2_progress_state(progress_rows=progress, topic_catalog_rows=catalog, latest_evaluation={"topic_id": "mlf_001", "status": "revise", "next_action": "retry_same_topic"})
    by_id = {row["topic_id"]: row for row in rows}
    assert active == "mlf_001"
    assert by_id["mlf_001"]["status"] == "needs_attention"
    assert by_id["capstone_ml_architect_001"]["status"] == "locked"
    assert by_id["dl_001"]["status"] == "locked"
