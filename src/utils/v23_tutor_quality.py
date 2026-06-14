"""V2.3 tutor-quality contract.

Purpose:
- Do not let a two-line concept note feed architect-level assessment.
- Expand every topic learning design at runtime into a deeper tutor path.
- Keep assessment evidence aligned to what is visibly taught.

This module is intentionally deterministic. It improves Supabase-authored and
bundled designs without needing another schema change.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, List, Optional


TOPIC_SAMPLE_ANSWERS: Dict[str, Dict[str, str]] = {
    "mlf_001": {
        "q1": (
            "An ML model learns statistical patterns from examples. It learns that certain inputs tend to map to certain outputs, "
            "but it does not understand the real-world meaning or cause behind those outputs. For example, a defect model may learn that humidity and machine speed are associated with scrap risk. That is useful for prediction, but it is not proof that the model understands why scrap happens."
        ),
        "q2": (
            "The likely missed boundary is distribution difference between the old training/validation data and the new factory. "
            "The model may have learned patterns from one factory setup, supplier mix, sensor behavior, or process condition, then faced a different production distribution. I would check segment performance on the new factory, compare feature distributions, and validate before trusting confident scores."
        ),
        "q3": (
            "Minimum controls are deployment-like validation, monitoring, and ownership. First, validate on data that matches the intended factory, time period, and operating conditions. Second, monitor input drift, prediction confidence, error rates, and segment performance after release. Third, assign an ML owner and quality/process owner who review breaches and decide whether to retrain, rollback, or add manual inspection."
        ),
        "q4": (
            "I would explain it like this: the model is not thinking like an engineer. It is matching patterns it has seen before. If past data shows certain sensor patterns before defects, it can flag similar cases. But if the factory changes, the same pattern may stop meaning the same thing. So prediction needs validation and monitoring, not blind trust."
        ),
    },
    "mlf_016": {
        "q1": (
            "A model score estimates relative risk; a decision threshold decides when the business acts. For example, a defect model may score one part as 0.42 risk. That score alone does not say inspect or release. The threshold converts the score into action. Changing the threshold changes alert volume, missed defects, and inspection workload, not the trained model itself."
        ),
        "q2": (
            "I would choose threshold 0.3 if missed defects are costly and inspection capacity can handle 125 alerts. It reduces precision from 85% to 60%, so more alerts will be false alarms, but recall improves from 35% to 75%, meaning fewer defects are missed. Since capacity is 140 alerts, the safer policy is the lower threshold with workload monitoring."
        ),
        "q3": (
            "The threshold may be too high for the business risk. High precision can mean the model alerts only on very obvious cases, so it misses many real defects. The response is not automatically retraining. I would review recall, false negatives, alert volume, and cost of missed defects, then lower or segment the threshold if inspection capacity allows."
        ),
        "q4": (
            "Threshold governance should record the missed-defect cost, false-alert cost, inspection capacity, minimum recall target, and approved alert volume. The quality owner and ML owner should approve the threshold before release. Monitoring should track recall, false negatives, precision, and alert volume by line or defect type. If recall drops or workload exceeds capacity, the owner reviews threshold, fallback inspection, or retraining evidence."
        ),
        "q5": (
            "I would tell a quality leader: the model gives a risk score, but the threshold decides when your team acts. A lower threshold catches more possible defects but creates more inspections. A higher threshold reduces workload but may miss defects. So the right threshold is not 0.5 by default. It must match defect cost, available inspection capacity, and agreed quality risk."
        ),
    },
}


def _clean(value: Any) -> str:
    return str(value or "").strip()


def _first_sentence(value: str, fallback: str = "") -> str:
    text = _clean(value)
    if not text:
        return fallback
    for sep in [". ", "? ", "! "]:
        if sep in text:
            return text.split(sep, 1)[0].strip() + sep.strip()
    return text


def _generic_sample_answer(design: Dict[str, Any], task: Dict[str, Any]) -> str:
    title = _clean(design.get("title")) or "this concept"
    objective = _clean(design.get("learning_objective"))
    example = design.get("worked_example") or {}
    scenario = _clean(example.get("scenario")) if isinstance(example, dict) else ""
    takeaway = _clean(example.get("takeaway")) if isinstance(example, dict) else ""
    architect = _clean(design.get("architect_extension"))
    qtype = _clean(task.get("type"))

    if qtype == "tiny_hands_on":
        return (
            f"I would start from the scenario evidence, then apply the concept directly. For {title}, the key point is: "
            f"{objective or takeaway}. In the example, {scenario or 'the metric or operating condition must be interpreted before deciding'}. "
            "The decision should state the trade-off, not just repeat the definition."
        )
    if qtype == "failure_diagnosis":
        return (
            f"The symptom should be separated from the likely cause. In {title}, the likely mechanism is: "
            f"{takeaway or objective}. I would check the relevant data, metric, segment, or process boundary before changing the model. "
            f"The fix should be tied to evidence, not guesswork."
        )
    if qtype == "architect_decision":
        return (
            f"I would govern {title} with a visible operating control. The control should state what evidence is checked, "
            f"who owns the decision, what trigger creates review, and what action follows. {architect or 'That turns the concept into a production decision rather than a theory answer.'}"
        )
    if qtype == "teachback":
        return (
            f"In simple terms, {title} means {objective or takeaway}. For a quality or manufacturing leader, the consequence is that "
            "a model output should not be treated as automatic truth. The team needs a clear decision rule and a review path when the model behaves differently from expected."
        )
    return (
        f"{title} means {objective or takeaway}. A practical example is: {scenario or 'a model result must be interpreted against the decision context'}. "
        "The important consequence is what can go wrong if the concept is ignored, and what control prevents that failure."
    )


def _build_expanded_steps(design: Dict[str, Any]) -> List[Dict[str, str]]:
    original = [s for s in (design.get("concept_steps") or []) if isinstance(s, dict)]
    title = _clean(design.get("title")) or "this topic"
    objective = _clean(design.get("learning_objective"))
    bridge = _clean(design.get("prerequisite_bridge"))
    example = design.get("worked_example") or {}
    scenario = _clean(example.get("scenario")) if isinstance(example, dict) else ""
    takeaway = _clean(example.get("takeaway")) if isinstance(example, dict) else ""
    misconception = _clean(design.get("misconception"))
    architect = _clean(design.get("architect_extension"))

    # Keep authored detailed lessons intact. Expand only shallow lessons.
    if len(original) >= 5:
        return original

    mechanism = " ".join(_clean(s.get("body")) for s in original if _clean(s.get("body")))
    mechanism = mechanism or objective

    steps = [
        {
            "heading": "Plain-English meaning",
            "body": objective or f"Understand {title} as a decision concept, not as vocabulary to memorize.",
        },
        {
            "heading": "What is actually changing",
            "body": mechanism or f"This concept changes how you judge model behavior, evidence, or production action for {title}.",
        },
        {
            "heading": "Concrete example",
            "body": f"{scenario} {takeaway}".strip() or "Use a small manufacturing example and state what the model output can and cannot prove.",
        },
        {
            "heading": "Common wrong answer",
            "body": misconception or "The weak answer stays at textbook definition level and never explains the production consequence.",
        },
        {
            "heading": "Architect translation",
            "body": architect or "Translate the concept into validation evidence, monitoring, trigger, owner, and action.",
        },
        {
            "heading": "What a 3-star answer must show",
            "body": "Give the definition in plain language, use one concrete example, state the consequence, and name one control. Do not write a thesis. Do not keyword-stuff.",
        },
        {
            "heading": "What a 5-star answer adds",
            "body": "Add the trade-off, evidence metric or check, owner, trigger, and action. That is architecture fluency.",
        },
    ]
    if bridge:
        steps.insert(0, {"heading": "Before this topic", "body": bridge})
    return steps


def _build_worked_examples(design: Dict[str, Any]) -> List[Dict[str, Any]]:
    existing = [w for w in (design.get("worked_examples") or []) if isinstance(w, dict)]
    if existing and all(_clean(w.get("title") or w.get("label")) for w in existing):
        return existing

    tasks = [t for t in (design.get("evidence_tasks") or []) if isinstance(t, dict)]
    title = _clean(design.get("title")) or "this topic"
    example = design.get("worked_example") or {}
    scenario = _clean(example.get("scenario")) if isinstance(example, dict) else ""
    takeaway = _clean(example.get("takeaway")) if isinstance(example, dict) else ""

    worked: List[Dict[str, Any]] = []
    for task in tasks[:3]:
        label = _clean(task.get("label")) or _clean(task.get("type")) or "Evidence task"
        purpose = _clean(task.get("purpose")) or "Prove the required reasoning."
        shape = _clean(task.get("response_shape")) or "Answer directly."
        focus = " · ".join(str(x) for x in (task.get("expected_focus") or []) if _clean(x))
        worked.append(
            {
                "title": f"How to answer: {label}",
                "steps": [
                    f"Start with the exact question. Do not write a generic {title} essay.",
                    f"Show this evidence: {focus or purpose}.",
                    f"Use this response shape: {shape}.",
                    f"Anchor it in the lesson example: {scenario or takeaway or 'one concrete production scenario'}.",
                    "Close with the consequence or operating action. That is what the evaluator should score.",
                ],
            }
        )
    return worked


def _enhance_tasks(design: Dict[str, Any]) -> List[Dict[str, Any]]:
    topic_id = _clean(design.get("topic_id"))
    samples = TOPIC_SAMPLE_ANSWERS.get(topic_id, {})
    enhanced: List[Dict[str, Any]] = []
    for task in (design.get("evidence_tasks") or []):
        if not isinstance(task, dict):
            continue
        item = deepcopy(task)
        qid = _clean(item.get("question_id"))
        item.setdefault("sample_answer", samples.get(qid) or _generic_sample_answer(design, item))
        item.setdefault("common_weak_answer", "A weak answer repeats vocabulary but does not state the scenario consequence or operating control.")
        item.setdefault("repair_instruction", "Rewrite as: direct answer + concrete example/evidence + consequence/action.")
        enhanced.append(item)
    return enhanced


def enhance_learning_design(learning_design: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if not isinstance(learning_design, dict) or not learning_design:
        return learning_design
    design = deepcopy(learning_design)
    if str(design.get("design_version") or "").endswith("v2_3"):
        return design

    design["design_version"] = f"{design.get('design_version') or 'unknown'}_v2_3"
    design["concept_steps"] = _build_expanded_steps(design)
    design["worked_examples"] = _build_worked_examples(design)
    design["evidence_tasks"] = _enhance_tasks(design)
    design["assessment_principle"] = (
        "Score only against what this lesson visibly teaches. A 3-star answer can be concise if it gives the mechanism, "
        "one concrete example/evidence point, and the decision consequence. Penalize technical falsehoods and copied scaffolds. "
        "Do not demand hidden vocabulary or thesis-length answers."
    )
    design["answer_quality_bar"] = {
        "three_star": "Plain definition + concrete example/evidence + consequence + one control where relevant.",
        "four_star": "Adds trade-off and explains why the selected evidence supports the decision.",
        "five_star": "Adds owner, trigger, monitoring signal, fallback/retrain/review action, and clear release decision.",
    }
    design["mastery_repair_prompts"] = design.get("mastery_repair_prompts") or [
        "Can I explain the concept in one simple sentence?",
        "Can I give one manufacturing or quality example?",
        "Can I state what goes wrong if this concept is ignored?",
        "Can I name one owner/action/control without turning it into a generic governance essay?",
    ]
    return design


def sample_answer_for_task(learning_design: Optional[Dict[str, Any]], question_id: str) -> Optional[str]:
    design = enhance_learning_design(learning_design)
    if not design:
        return None
    for task in design.get("evidence_tasks", []) or []:
        if isinstance(task, dict) and str(task.get("question_id")) == str(question_id):
            sample = _clean(task.get("sample_answer"))
            return sample or None
    return None
