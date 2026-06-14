from src.utils.v2_learning_policy import (
    all_ml_lessons_mastered,
    capstone_mastered,
    classify_progress_row,
    select_active_topic,
    should_complete_from_visible_gate,
)


def row(topic_id, concept=3, practical=3, architect=3, communication=3, status="locked", attempt_count=1, sequence_no=1):
    return {
        "topic_id": topic_id,
        "last_score_conceptual": concept,
        "last_score_practical": practical,
        "last_score_architect": architect,
        "last_score_communication": communication,
        "status": status,
        "attempt_count": attempt_count,
        "sequence_no": sequence_no,
    }


def test_visible_gate_all_3_completes():
    assert should_complete_from_visible_gate(
        "mlf_001",
        {
            "conceptual_clarity": 3,
            "practical_reasoning": 3,
            "architect_reasoning": 3,
            "communication": 3,
        },
    )


def test_visible_gate_any_2_blocks():
    assert not should_complete_from_visible_gate(
        "mlf_001",
        {
            "conceptual_clarity": 2,
            "practical_reasoning": 3,
            "architect_reasoning": 3,
            "communication": 3,
        },
    )


def test_all_ml_lessons_mastered_requires_every_mlf_min_3():
    rows = [row("mlf_001"), row("mlf_002", architect=2)]
    assert not all_ml_lessons_mastered(rows)


def test_latest_failed_redo_stays_active():
    rows = [
        row("mlf_001", concept=2, practical=2, architect=2, communication=2, status="needs_attention", sequence_no=1),
        row("mlf_016", status="unlocked", sequence_no=16),
    ]
    latest = {"topic_id": "mlf_001", "status": "revise", "next_action": "retry_same_topic"}
    assert select_active_topic(rows, latest) == "mlf_001"


def test_dl_locked_until_capstone_mastered():
    rows = [row("capstone_ml_architect_001", concept=2, status="locked"), row("dl_001", status="locked")]
    assert not capstone_mastered(rows)
    assert classify_progress_row(rows[1], rows) == "locked"
