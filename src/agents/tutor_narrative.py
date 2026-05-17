from __future__ import annotations

from typing import Any, Dict, List, Optional

from src.blueprints.advanced_ml import get_blueprint


def _as_list(value: Any) -> List[str]:
    if not value:
        return []
    if isinstance(value, list):
        return [str(item) for item in value if str(item or "").strip()]
    return [str(value)]


ADVANCED_TUTOR_EXPANSIONS: Dict[str, Dict[str, Any]] = {
    "checkpoint_ml_foundations_001": {
        "teacher_walkthrough": "This checkpoint is not another lesson. It checks whether the foundations behave like one system. A valid model decision needs a clean target, a clean split, a baseline, no leakage, the right metric, and a go-live control. If one link is weak, the model may look impressive while being unsafe.",
        "safe_vs_unsafe": [
            "Unsafe: approve a defect model because accuracy is high.",
            "Safe: inspect confusion matrix, recall for defects, leakage risk, threshold policy, and fallback owner before go-live.",
        ],
        "mini_checks": [
            "If accuracy is high but recall is low, what business failure is being hidden?",
            "If a feature is created after the event, why does it invalidate evaluation?",
            "What baseline proves, and what it does not prove?",
        ],
    },
    "mlf_011": {
        "teacher_walkthrough": "Model selection is not a beauty contest between algorithms. It is a production decision. You are choosing the model whose errors, cost, latency, interpretability, maintenance load, and segment stability match the business problem. A model with the best average score can still be the wrong choice if it collapses on a critical plant, product, or defect type.",
        "safe_vs_unsafe": [
            "Unsafe: choose the model with the highest training score or best aggregate validation score.",
            "Safe: compare candidates against baseline, validation/test metrics, segment stability, latency, explainability, and monitoring feasibility.",
        ],
        "mini_checks": [
            "Which matters more for go-live: average accuracy or stable recall on high-risk segments?",
            "What production constraint could make a lower-scoring model the better choice?",
            "How would you prove a complex model adds value over baseline?",
        ],
    },
    "mlf_012": {
        "teacher_walkthrough": "Feature engineering decides what signal the model is allowed to see. Feature contracts decide whether that signal is valid enough to trust. A feature can be mathematically useful during training and still be unusable in production if it arrives late, changes units, has invalid ranges, or is calculated differently online.",
        "safe_vs_unsafe": [
            "Unsafe: add more features because more columns feel like more intelligence.",
            "Safe: check signal value, availability at prediction time, unit/range validity, freshness, and training-inference parity.",
        ],
        "mini_checks": [
            "Can this feature exist at prediction time?",
            "What range, unit, type, and freshness should this feature obey?",
            "What happens if this feature silently changes from Celsius to Fahrenheit?",
        ],
    },
    "mlf_013": {
        "teacher_walkthrough": "Categorical encoding is not just converting words into numbers. It is preserving meaning. Nominal values such as station, supplier, or fault type have no natural order. If you encode them as 1, 2, 3, the model may learn fake ranking. Ordinal values such as low, medium, high can use order only when that order is real. Production adds the hard part: the encoder fitted during training must be reused during inference, and unseen categories need a planned path.",
        "safe_vs_unsafe": [
            "Unsafe: label-encode nominal categories and let the model infer fake order.",
            "Safe: choose encoding based on category meaning, persist the fitted encoder, handle unknowns explicitly, and monitor unknown-category rate.",
        ],
        "mini_checks": [
            "Is this category nominal, ordinal, binary, or high-cardinality?",
            "What happens when a new category appears after training?",
            "Is retraining the immediate runtime control or a later review action?",
        ],
    },
    "mlf_014": {
        "teacher_walkthrough": "Scaling changes the ruler. Standardization tells you how far a value is from the training average. The key is not cosmetic preprocessing. The key is geometry. Distance-based models compare points; gradient-based models optimize weights; projection methods look for directions of variance. Large-scale features can dominate these behaviors even when they are not more important.",
        "safe_vs_unsafe": [
            "Unsafe: fit scaler on full data, then split train/test.",
            "Safe: split first, fit scaler only on train, persist it, and transform validation/test/production with that same fitted transformer.",
            "Unsafe: refit scaler live when production values go outside training range.",
            "Safe: monitor out-of-range values and trigger review or retraining through a controlled process.",
        ],
        "mini_checks": [
            "For min-max scaling, which values define the ruler?",
            "For z-score standardization, what do mean and standard deviation come from?",
            "Why are KNN/SVM/PCA/neural networks more scale-sensitive than trees?",
        ],
    },
    "mlf_015": {
        "teacher_walkthrough": "Regularization is a discipline mechanism. It limits how aggressively the model can use its freedom. Without it, a flexible model may treat noise, rare quirks, or coincidental sensor spikes as important. With too much regularization, the model becomes too cautious and misses real patterns. The lesson is not 'regularization prevents overfitting'. The real lesson is controlled complexity using validation evidence.",
        "safe_vs_unsafe": [
            "Unsafe: increase regularization blindly because validation performance is weak.",
            "Safe: compare train vs validation behavior, tune regularization strength, and check whether the model is overfitting or underfitting.",
        ],
        "mini_checks": [
            "What does a high train score but weak validation score suggest?",
            "What can happen if regularization is too strong?",
            "Why does regularization not fix leakage or bad labels?",
        ],
    },
    "mlf_016": {
        "teacher_walkthrough": "A classifier usually gives a score, not a final business action. The threshold turns that score into a decision. A 0.5 default threshold is just a default, not a quality policy. If missed defects are expensive, you may lower the threshold to catch more defects. That raises recall but may increase false alarms. Threshold tuning is where model behavior meets operating cost.",
        "safe_vs_unsafe": [
            "Unsafe: accept the default 0.5 threshold without checking false-negative cost.",
            "Safe: inspect precision-recall trade-off, cost matrix, alert volume, and define a threshold owner.",
        ],
        "mini_checks": [
            "If missed defects are costly, which metric usually gets priority?",
            "What operational cost rises when you lower the threshold?",
            "Who owns threshold changes after go-live?",
        ],
    },
    "mlf_017": {
        "teacher_walkthrough": "Class imbalance is not only a data-count problem. It is an objective mismatch problem. A model can look strong because it predicts the majority class well while failing the rare class the business actually cares about. The fix is not automatically resampling. The fix starts with defining the cost of missing the minority class and choosing metrics, thresholds, and training strategy around that risk.",
        "safe_vs_unsafe": [
            "Unsafe: report accuracy on an imbalanced problem and declare success.",
            "Safe: inspect minority recall/precision, confusion matrix, threshold, class weights or resampling strategy, and validation by segment.",
        ],
        "mini_checks": [
            "Which error matters more: false negative or false positive?",
            "Could resampling distort probability calibration?",
            "Why should threshold tuning be considered along with class weights?",
        ],
    },
    "mlf_018": {
        "teacher_walkthrough": "Error analysis is where aggregate scores become diagnosis. A model can have acceptable overall performance but fail badly for one plant, supplier, product type, shift, or defect family. Error analysis slices mistakes to find patterns. The architect value is not just saying 'score is low'. It is turning failure clusters into data fixes, feature fixes, label fixes, threshold fixes, or process fixes.",
        "safe_vs_unsafe": [
            "Unsafe: look only at overall F1 or accuracy.",
            "Safe: slice errors by meaningful business segments and trace whether failures come from data coverage, labels, features, threshold, or drift.",
        ],
        "mini_checks": [
            "Which segment is failing even if the average looks good?",
            "Are false negatives concentrated in one defect type?",
            "What action follows from each error pattern?",
        ],
    },
    "mlf_019": {
        "teacher_walkthrough": "Interpretability helps explain model behavior, but it does not prove causality or correctness. A feature importance chart can show which features influenced predictions, not whether the model is safe. Explanations are evidence for review, debugging, governance, and stakeholder trust. They are not a replacement for validation, leakage checks, monitoring, or domain review.",
        "safe_vs_unsafe": [
            "Unsafe: treat SHAP or feature importance as proof that the model is right.",
            "Safe: use explanations to investigate behavior, compare against domain expectations, and decide what additional validation is needed.",
        ],
        "mini_checks": [
            "Does an explanation prove causation?",
            "Is the explanation global or local?",
            "What would you do if explanations contradict domain knowledge?",
        ],
    },
    "mlf_020": {
        "teacher_walkthrough": "Monitoring is not a dashboard decoration. It is the operating system around the model. Data drift means inputs changed. Concept drift means the relationship between inputs and target changed. Performance drift means model outcomes worsened. Each signal needs a trigger, an owner, and an action. Without that, monitoring becomes a chart nobody is accountable for.",
        "safe_vs_unsafe": [
            "Unsafe: monitor everything with no thresholds or owner.",
            "Safe: define drift/performance signals, alert thresholds, investigation owner, fallback path, and retraining decision rule.",
        ],
        "mini_checks": [
            "Which signal tells you inputs changed?",
            "Which signal tells you the target relationship changed?",
            "What action happens when an alert fires?",
        ],
    },
}


def get_tutor_narrative(topic_id: str) -> Optional[Dict[str, Any]]:
    """Build a teacher-like narrative from the expert blueprint.

    This is intentionally not a field dump. The blueprint remains the source of
    truth, but this renderer turns it into a learning path: intuition, mechanism,
    worked example, safe/unsafe contrast, comprehension checks, architect controls,
    and mission-specific prep.
    """
    bp = get_blueprint(topic_id)
    if not bp:
        return None

    expansion = ADVANCED_TUTOR_EXPANSIONS.get(topic_id, {})
    missions = bp.get("missions", []) or []
    mission_prep = []
    for mission in missions:
        qid = str(mission.get("question_id", "")).upper()
        qtype_raw = str(mission.get("type", "mission"))
        qtype = qtype_raw.replace("_", " ").title()
        expected = _as_list(mission.get("expected_focus", []))
        mission_prep.append(_build_mission_prep(qid, qtype, qtype_raw, mission, expected, bp, expansion))

    sections: List[Dict[str, Any]] = [
        {
            "heading": "Start Here: The Intuition",
            "body": _join_teacher_text(bp.get("plain_intuition", ""), expansion.get("teacher_walkthrough", "")),
            "style": "good",
        },
        {
            "heading": "Precise Definition",
            "body": bp.get("definition", ""),
            "style": "normal",
        },
        {
            "heading": "Why This Concept Exists",
            "body": bp.get("why_it_exists", ""),
            "style": "normal",
        },
        {
            "heading": "Slow Walkthrough: What Actually Changes",
            "body": _teacher_walkthrough(bp, expansion),
            "style": "good",
        },
        {
            "heading": "Worked Example, Step by Step",
            "body": _worked_example(bp, expansion),
            "style": "normal",
        },
    ]

    safe_vs_unsafe = _as_list(expansion.get("safe_vs_unsafe", []))
    if safe_vs_unsafe:
        sections.append(
            {
                "heading": "Unsafe vs Safe Pattern",
                "body": safe_vs_unsafe,
                "style": "risk",
            }
        )

    mini_checks = _as_list(expansion.get("mini_checks", []))
    if mini_checks:
        sections.append(
            {
                "heading": "Pause and Check Yourself",
                "body": mini_checks,
                "style": "good",
            }
        )

    sections.extend(
        [
            {
                "heading": "Where This Matters Most",
                "body": bp.get("when_matters", ""),
                "style": "normal",
            },
            {
                "heading": "Where This Matters Less",
                "body": bp.get("when_less", ""),
                "style": "normal",
            },
            {
                "heading": "Nuances You Should Not Miss",
                "body": _as_list(bp.get("nuances", [])),
                "style": "good",
            },
            {
                "heading": "Common Traps",
                "body": _as_list(bp.get("common_confusions", [])),
                "style": "risk",
            },
            {
                "heading": "Architect Translation",
                "body": _as_list(bp.get("architect_implications", [])),
                "style": "good",
            },
            {
                "heading": "System Design Controls",
                "body": _as_list(bp.get("system_design_controls", [])),
                "style": "normal",
            },
            {
                "heading": "Mission Answer Frame",
                "body": _as_list(bp.get("mission_answer_frame", [])),
                "style": "normal",
            },
            {
                "heading": "Do Not Waste Words On This",
                "body": _as_list(bp.get("do_not_waste_words", [])),
                "style": "risk",
            },
        ]
    )

    return {
        "topic_id": bp["topic_id"],
        "title": bp["title"],
        "sections": sections,
        "mission_prep": mission_prep,
    }


def _join_teacher_text(primary: Any, expansion: Any) -> str:
    primary_text = str(primary or "").strip()
    expansion_text = str(expansion or "").strip()
    if primary_text and expansion_text and expansion_text not in primary_text:
        return f"{primary_text}\n\n{expansion_text}"
    return expansion_text or primary_text


def _teacher_walkthrough(bp: Dict[str, Any], expansion: Dict[str, Any]) -> str:
    mechanism = str(bp.get("core_mechanism", "")).strip()
    if not mechanism:
        mechanism = "Use the topic mechanism before jumping to production-risk language."

    title = str(bp.get("title", "")).lower()
    if "scaling" in title:
        return (
            f"{mechanism}\n\n"
            "Slow it down: fitting is the learning step for the transformer. It learns min, max, mean, or standard deviation. "
            "Transforming is the application step. Validation, test, and production data should not teach the transformer anything. "
            "They should only be transformed using the training-fitted transformer. That fit/transform boundary is the actual leakage boundary."
        )
    if "encoding" in title:
        return (
            f"{mechanism}\n\n"
            "Slow it down: the encoding method changes what meaning the model can infer. One-hot says categories are separate flags. "
            "Ordinal encoding says the order matters. Unknown handling says production is allowed to survive categories that training did not see."
        )
    if "threshold" in title:
        return (
            f"{mechanism}\n\n"
            "Slow it down: the model score estimates risk; the threshold decides action. Changing the threshold does not retrain the model. "
            "It changes the operating point, which changes false positives, false negatives, workload, and business risk."
        )
    if "regularization" in title:
        return (
            f"{mechanism}\n\n"
            "Slow it down: regularization does not make the data cleaner. It changes the training objective so the model pays a cost for complexity. "
            "The question is whether that cost reduces noise-fitting without suppressing real signal."
        )
    if "imbalance" in title:
        return (
            f"{mechanism}\n\n"
            "Slow it down: a model can optimize the majority class and still fail the business. The mechanism is not only fewer examples; "
            "it is that the training objective and chosen metric may not value the minority error enough."
        )
    return mechanism


def _worked_example(bp: Dict[str, Any], expansion: Dict[str, Any]) -> str:
    worked = str(bp.get("worked_example", "")).strip()
    title = str(bp.get("title", "")).lower()
    if "scaling" in title:
        return (
            f"{worked}\n\n"
            "Use this pattern for the mission: first find min and max, then apply min-max scaling to each value. "
            "For z-score standardization, find the training mean and training standard deviation, then compute (x - mean) / std. "
            "Show two examples clearly; then state that the same saved transformer must be reused downstream."
        )
    if "threshold" in title:
        return (
            f"{worked}\n\n"
            "Use this pattern: compare threshold options by recall, precision, and operational load. Then choose the threshold that fits the business cost, not the one that sounds mathematically neat."
        )
    if "imbalance" in title:
        return (
            f"{worked}\n\n"
            "Use this pattern: compute what the model catches in the minority class, then explain why aggregate accuracy is not enough."
        )
    return worked


def _build_mission_prep(
    qid: str,
    qtype: str,
    qtype_raw: str,
    mission: Dict[str, Any],
    expected: List[str],
    bp: Dict[str, Any],
    expansion: Dict[str, Any],
) -> Dict[str, Any]:
    controls = _as_list(bp.get("system_design_controls", []))[:4]
    mechanism = str(bp.get("core_mechanism", "")).strip()
    first_mechanism_sentence = mechanism.split(".")[0].strip() + "." if mechanism else "Use the topic-specific mechanism, not generic production language."

    if qtype_raw == "concept_check":
        tested = "Can you define the concept and explain the specific mechanism without drifting into generic production-risk filler?"
        answer_shape = "80-120 words: precise definition → mechanism → one example → why the distinction matters."
        avoid = "Do not start with a long generic ML explanation. Do not repeat every control from the architect section."
    elif qtype_raw == "tiny_hands_on":
        tested = "Can you apply the concept to the numbers or scenario, then interpret the result?"
        answer_shape = "Show the method first, calculate or compare, then add one practical interpretation."
        avoid = "Do not hide behind theory. Use the numbers or concrete objects in the question."
    elif qtype_raw == "failure_diagnosis":
        tested = "Can you separate symptom, root mechanism, evidence, and prevention?"
        answer_shape = "Symptom → specific mechanism → evidence to inspect → prevention control."
        avoid = "Do not only say 'the model failed in production' or 'there was leakage' without naming how."
    elif qtype_raw == "architect_decision":
        tested = "Can you convert the concept into concrete pipeline/system controls?"
        answer_shape = "Decision rule → controls → monitoring signal → owner/response."
        avoid = "Do not just say 'monitor and retrain'. Name the control and trigger."
    elif qtype_raw == "teachback":
        tested = "Can you explain the concept clearly to an interviewer or stakeholder without overexplaining?"
        answer_shape = "Simple explanation → one real example → risk → architect control."
        avoid = "Do not sound like a textbook. Keep it business-facing and specific."
    else:
        tested = "Can you apply the lesson mechanism to the mission scenario?"
        answer_shape = "Definition → example → failure mode → control."
        avoid = "Do not write an essay."

    must_include = expected[:] if expected else []
    if not must_include:
        must_include = [first_mechanism_sentence]
    if qtype_raw in {"architect_decision", "failure_diagnosis"} and controls:
        must_include.extend([f"Control: {item}" for item in controls[:2]])

    return {
        "title": f"{qid} . {qtype}",
        "question": mission.get("question", ""),
        "tested_skill": tested,
        "must_include": must_include[:6],
        "answer_shape": answer_shape,
        "avoid": avoid,
        "how_to_answer": _mission_answer_guidance(qtype_raw, bp, expansion),
    }


def _mission_answer_guidance(question_type: str, bp: Dict[str, Any], expansion: Dict[str, Any]) -> str:
    title = str(bp.get("title", "")).lower()
    if question_type == "concept_check":
        return "Use one precise definition, one mechanism, and one consequence. Stop before it becomes an essay."
    if question_type == "tiny_hands_on":
        if "scaling" in title:
            return "For calculation missions, show the formula and two clear examples. Do not spend the answer explaining all of ML preprocessing."
        return "Use the numbers or scenario first, then interpret. Do not hide behind theory."
    if question_type == "failure_diagnosis":
        return "Write symptom → mechanism → evidence → prevention. Avoid generic 'model failed in production' wording."
    if question_type == "architect_decision":
        controls = ", ".join((bp.get("system_design_controls") or [])[:4])
        return f"Name the controls and ownership. Useful controls here include: {controls}."
    if question_type == "teachback":
        return "Explain simply, use one business example, and finish with the practical control."
    return "Use definition, example, failure mode, and control."
