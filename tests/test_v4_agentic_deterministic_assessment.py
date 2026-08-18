from __future__ import annotations

import statistics

from src.blueprints.agentic_ai import AGENTIC_AI_DESIGNS, get_agentic_learning_design
from src.schemas import UserAnswer
from src.utils.deterministic_written_evaluator import build_deterministic_evaluation, evaluate_rubric_evidence
from src.utils.learning_design_registry import resolve_learning_design
from src.utils.v2_learning_policy import normal_lesson_contract
from src.utils.v3_assessment_policy import normalize_mcq_items


AIA004_PREVIOUS_ANSWER = """While building a procurement agent that is working on a task of order status checking, we should define a plan schema: 1. define a clear goal - act as a procurement agent which specialises in understanding user problem, extract relevant information using provided tools, take human approval and respond to users. 2. Steps - perform the sequence of steps and database read queries. Ask for user name, product details and/or order number. Query database to get the latest status. Respond to users with the status 3. Evaluation steps - Is the user asking for information it is not authorised to, the information sought is verified, authentic and accurate, does it need a human approval while sharing the order status. 4. No database write access is given to the agent.

This way the larger goal is decomposed into smaller tasks for better governance and decision making. Any financial transaction approval sits with humans. In case of deviation guardrails to be defined"""


def test_agentic_bank_has_ten_authored_mcqs_per_topic():
    assert len(AGENTIC_AI_DESIGNS) == 10
    forbidden = {
        "Only a vendor name",
        "A longer prompt",
        "A more confident answer",
        "Only a demo video",
        "Only the model name",
        "Only token count",
    }
    for topic_id, design in AGENTIC_AI_DESIGNS.items():
        checks = design["knowledge_checks"]
        assert len(checks) == 10, topic_id
        assert sum(1 for item in checks if item.get("is_critical")) >= 3
        for item in checks:
            assert len(item["options"]) == 4
            assert not forbidden.intersection(item["options"])


def test_longest_option_is_not_a_reliable_answer_strategy():
    total = 0
    unique_longest_correct = 0
    for design in AGENTIC_AI_DESIGNS.values():
        for item in design["knowledge_checks"]:
            lengths = [len(option.split()) for option in item["options"]]
            correct = int(item["answer_index"])
            total += 1
            if lengths[correct] == max(lengths) and lengths.count(max(lengths)) == 1:
                unique_longest_correct += 1
    assert unique_longest_correct / total <= 0.20


def test_runtime_shuffle_balances_answer_positions():
    design = get_agentic_learning_design("aia_004")
    items = normalize_mcq_items(design["knowledge_checks"], seed_context="test_run_aia_004")
    positions = [int(item["answer_index"]) for item in items]
    assert len(items) == 10
    assert max(positions.count(i) for i in range(4)) <= 3


def test_aia004_previous_answer_gets_credit_for_explicit_evidence():
    design = get_agentic_learning_design("aia_004")
    audit = evaluate_rubric_evidence(design, AIA004_PREVIOUS_ANSWER)
    required = {item["id"]: item for item in audit["required"]}
    assert required["mechanism"]["matched"]
    assert required["example"]["matched"]
    assert required["risk"]["matched"]
    assert required["control"]["matched"]

    evaluation, _ = build_deterministic_evaluation(
        learning_design=design,
        user_answers=[UserAnswer(question_id="q1", answer=AIA004_PREVIOUS_ANSWER)],
        mcq_result={"passed": True, "score_pct": 100},
    )
    assert evaluation.decision == "pass"
    assert evaluation.scores.practical_reasoning >= 3
    assert not any("Missing published requirement" in item for item in evaluation.weak_spots)


def test_missing_risk_is_not_silently_passed():
    design = get_agentic_learning_design("aia_004")
    answer = (
        "In a procurement agent, planning breaks the order-status goal into steps: verify the user, "
        "capture the order number, call the read-only order API and return the status. "
        "The runtime allows only the read-only tool and validates the order result before responding. "
        "The process is bounded and uses a clear goal and tool sequence."
    )
    evaluation, audit = build_deterministic_evaluation(
        learning_design=design,
        user_answers=[UserAnswer(question_id="q1", answer=answer)],
        mcq_result={"passed": True, "score_pct": 100},
    )
    risk = next(item for item in audit["required"] if item["id"] == "risk")
    assert not risk["matched"]
    assert evaluation.decision == "revise"


def test_registry_prefers_repository_authored_agentic_design():
    design = resolve_learning_design("aia_004")
    assert design["design_version"] == "mlos_v4_deterministic_agentic_2026_08_17"
    assert design["assessment_mode"] == "v4_deterministic_mcq_plus_published_rubric"


def test_normal_lesson_contract_has_one_written_task():
    assert normal_lesson_contract()["written_evidence_tasks"] == 1
