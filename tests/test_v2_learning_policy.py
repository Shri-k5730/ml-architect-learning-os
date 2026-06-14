from src.utils.v2_learning_policy import select_active_topic, should_complete_from_visible_gate


def test_failed_latest_redo_wins_over_later_unlocked():
    rows = [
        {"topic_id": "mlf_001", "status": "needs_attention", "sequence_no": 1},
        {"topic_id": "mlf_016", "status": "unlocked", "sequence_no": 16},
    ]
    latest = {"topic_id": "mlf_001", "status": "revise", "next_action": "retry_same_topic"}
    assert select_active_topic(rows, latest) == "mlf_001"


def test_visible_gate_blocks_score_2():
    assert not should_complete_from_visible_gate("mlf_001", {
        "conceptual_clarity": 2,
        "practical_reasoning": 3,
        "architect_reasoning": 3,
        "communication": 3,
    })


def test_visible_gate_all_3_passes():
    assert should_complete_from_visible_gate("mlf_001", {
        "conceptual_clarity": 3,
        "practical_reasoning": 3,
        "architect_reasoning": 3,
        "communication": 3,
    })
