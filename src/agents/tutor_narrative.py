from __future__ import annotations

from typing import Any, Dict, List


def _list(value: Any) -> List[str]:
    if not value:
        return []
    if isinstance(value, list):
        return [str(item) for item in value if str(item or '').strip()]
    return [str(value)]


def _mission_prep_from_blueprint(blueprint: Dict[str, Any]) -> List[Dict[str, Any]]:
    prep: List[Dict[str, Any]] = []
    for idx, mission in enumerate(blueprint.get("missions", []) or [], start=1):
        qtype = str(mission.get("type", "mission")).replace("_", " ").title()
        focus = _list(mission.get("expected_focus"))
        if not focus:
            focus = ["Use the concept mechanism, then state the practical or architect implication."]
        prep.append(
            {
                "title": f"Mission {idx}: {qtype}",
                "body": focus,
            }
        )
    return prep


def _generic_narrative(topic_id: str, blueprint: Dict[str, Any]) -> Dict[str, Any]:
    title = blueprint.get("title", topic_id)
    common_confusions = _list(blueprint.get("common_confusions"))
    nuances = _list(blueprint.get("nuances"))
    system_controls = _list(blueprint.get("system_controls"))
    architect_implications = _list(blueprint.get("architect_implications"))

    return {
        "intuition": (
            f"Treat {title} as a specific lever in the ML system, not as another generic production-risk topic. "
            "First understand what changes inside the data, model, metric, or decision boundary. Only then translate it into architecture controls."
        ),
        "precise_definition": blueprint.get("definition", ""),
        "why_it_exists": blueprint.get("why_it_exists", ""),
        "mechanism_walkthrough": blueprint.get("core_mechanism", ""),
        "worked_example_slow": blueprint.get("worked_example", ""),
        "model_sensitivity": [
            "Ask which model family, metric, or decision process is sensitive to this concept.",
            "Do not answer only with 'it may fail in production'. Explain the mechanism that creates the failure.",
        ],
        "nuances": nuances,
        "common_traps": common_confusions,
        "architect_translation": architect_implications,
        "system_controls": system_controls,
        "mission_prep": _mission_prep_from_blueprint(blueprint),
        "avoid_when_answering": [
            "Do not repeat the definition in every mission.",
            "Do not use generic phrases like 'model fails in production' unless you also name the specific mechanism.",
            "Do not write an essay. Use: definition, example, failure mechanism, control.",
        ],
    }


_MLF014_MISSION_PREP = [
    {
        "title": "Mission 1: Concept Check",
        "body": [
            "Define min-max scaling and z-score standardization separately.",
            "Say why the distinction matters: they answer different numeric questions.",
            "Add one model-family example, such as KNN/SVM/neural networks being scale-sensitive.",
        ],
    },
    {
        "title": "Mission 2: Tiny Hands On",
        "body": [
            "Do not write theory first. Start with min=50 and max=100.",
            "Use scaled(x) = (x - 50) / 50 for each value.",
            "Then compute mean and standard deviation, and apply z = (x - mean) / std.",
            "Show the method clearly. Rounded values are acceptable if the logic is explicit.",
        ],
    },
    {
        "title": "Mission 3: Failure Diagnosis",
        "body": [
            "Name the observed problem: test/future information influenced preprocessing.",
            "Name the root cause: scaler/standardizer was fitted on full data instead of training data only.",
            "State why metrics became optimistic: validation/test data affected transformation parameters.",
            "State the fix: fit on train, transform validation/test/production using saved transformer.",
        ],
    },
    {
        "title": "Mission 4: Architect Decision",
        "body": [
            "Design the pipeline: split data first, fit transformer on training only, persist transformer with model.",
            "Use the same transformer for validation, test, batch inference, and online inference.",
            "Add controls: feature range contract, preprocessing unit test, out-of-range monitoring, artifact versioning.",
        ],
    },
    {
        "title": "Mission 5: Teachback",
        "body": [
            "Explain simply: scaling changes the ruler; standardization compares values to the training average.",
            "Use one concrete example, then explain fit-vs-transform leakage.",
            "Avoid a formula dump unless the interviewer asks for calculation.",
        ],
    },
]


def _mlf014(blueprint: Dict[str, Any]) -> Dict[str, Any]:
    base = _generic_narrative("mlf_014", blueprint)
    base.update(
        {
            "intuition": (
                "Scaling is not cosmetic cleanup. It changes the numeric ruler the model uses. "
                "Standardization is different: it asks how far a value is from the training average. "
                "The key architect boundary is fit versus transform: learn preprocessing parameters from training data only, then reuse them everywhere else."
            ),
            "precise_definition": (
                "Min-max scaling maps values into a chosen range, usually 0 to 1. "
                "Z-score standardization maps values into units of standard deviation around the training mean. "
                "Pipeline leakage happens when preprocessing learns min, max, mean, or standard deviation from validation, test, or future data."
            ),
            "why_it_exists": (
                "Many models compare numeric distances or optimize numeric weights. If one feature ranges from 0 to 100000 and another ranges from 0 to 1, the large-scale feature can dominate. "
                "Preprocessing exists to make the numeric representation fairer or easier for the model to learn from."
            ),
            "mechanism_walkthrough": (
                "There are two actions: fit and transform. Fit means learning parameters such as min, max, mean, and standard deviation. Transform means applying those learned parameters. "
                "The training set is the only data allowed to teach the scaler. Validation, test, and production data must be transformed using the saved training scaler. "
                "If you fit on the full dataset, information from data that should be unseen changes the preprocessing parameters, so evaluation is no longer clean."
            ),
            "worked_example_slow": (
                "For [50, 60, 70, 80, 90, 100], min=50 and max=100. Min-max scaling uses (x-min)/(max-min), so 50 becomes 0, 70 becomes 0.4, and 100 becomes 1. "
                "For z-score standardization, first compute the training mean and standard deviation. The mean is 75. A value below 75 gets a negative z-score, 75 is near 0, and a value above 75 gets a positive z-score. "
                "The mission may ask for all rows, but the pattern is the real concept."
            ),
            "model_sensitivity": [
                "Usually sensitive: KNN, SVM, PCA, logistic regression, linear models with regularization, neural networks, and gradient-based models.",
                "Usually less sensitive to feature scale: decision trees, random forests, and many gradient-boosted trees. Pipeline consistency still matters even for these models.",
                "If the model uses distances, gradients, projections, or regularized weights, scaling/standardization can materially change behavior.",
            ],
            "nuances": [
                "People often say normalization when they mean standardization. In your answer, name the exact operation: min-max scaling or z-score standardization.",
                "Out-of-range production values do not mean you refit the scaler live. They mean you monitor, flag, and decide through governance.",
                "The right preprocessing depends on model family and data distribution. It is not a universal checkbox.",
            ],
            "common_traps": [
                "Fitting scalers on the full dataset before train/test split.",
                "Fitting separate scalers on train, validation, and test sets.",
                "Saying 'normalization prevents production failure' without explaining feature magnitude or leakage mechanism.",
                "Forgetting to persist the transformer artifact with the model.",
            ],
            "architect_translation": [
                "Split data before preprocessing is fitted.",
                "Package preprocessing and model together, ideally as a pipeline artifact.",
                "Version the transformer with the model so inference uses the same transformation learned during training.",
                "Monitor production feature ranges against training ranges, but do not silently refit in production.",
            ],
            "system_controls": [
                "Train-only fit rule for all scalers/standardizers.",
                "Saved preprocessing artifact with version and model linkage.",
                "Unit test proving validation/test data is transformed, not fitted.",
                "Feature range and unit contracts.",
                "Out-of-training-range monitoring with owner and response path.",
            ],
            "mission_prep": _MLF014_MISSION_PREP,
            "avoid_when_answering": [
                "Do not write 'scaling and normalization are important for production' as the main answer. That is too vague.",
                "Do not call z-score standardization 'normalization' unless you explain mean and standard deviation.",
                "Do not spend half the answer on generic leakage. Name the exact leak: fitting preprocessing on non-training data.",
                "Do not say refit live in production. Use saved transformer, monitoring, and governed retraining review.",
            ],
        }
    )
    return base


_MLF013_MISSION_PREP = [
    {
        "title": "Mission 1: Concept Check",
        "body": [
            "Define encoding as preserving categorical meaning in numeric form, not merely converting text to numbers.",
            "Separate nominal, ordinal, binary, and high-cardinality cases.",
            "Mention unseen-category handling briefly but concretely.",
        ],
    },
    {
        "title": "Mission 2: Tiny Hands On",
        "body": [
            "Show the one-hot columns explicitly.",
            "For a new category, say whether you use unknown bucket, safe ignore, or contract violation route.",
            "Do not jump directly to retraining as the first runtime control.",
        ],
    },
    {
        "title": "Mission 3: Failure Diagnosis",
        "body": [
            "Symptom: new category caused bad or failed prediction.",
            "Cause: production encoder did not have a defined mapping for unseen category.",
            "Fix: persist fitted encoder, explicit unknown strategy, monitor unknown rate.",
        ],
    },
    {
        "title": "Mission 4: Architect Decision",
        "body": [
            "Classify categorical fields first.",
            "Choose encoding by data type and model family.",
            "Define encoder artifact, feature contract, unknown-rate monitor, and retraining trigger.",
        ],
    },
    {
        "title": "Mission 5: Teachback",
        "body": [
            "Use simple language: numbers can accidentally create fake meaning.",
            "Give one nominal example and one ordinal example.",
            "Close with production risk: unseen categories need planned behavior before go-live.",
        ],
    },
]


def _mlf013(blueprint: Dict[str, Any]) -> Dict[str, Any]:
    base = _generic_narrative("mlf_013", blueprint)
    base.update(
        {
            "intuition": (
                "Encoding is not just turning words into numbers. It is preserving the meaning of categories while making them usable by a model. "
                "The danger is that a careless encoding can invent meaning the data never had."
            ),
            "precise_definition": (
                "Categorical encoding converts labels into numeric representations. Safe encoding keeps the semantics intact, avoids leakage, and defines what happens when production sends a category the training data never saw."
            ),
            "mechanism_walkthrough": (
                "Nominal categories have no order, so one-hot or similar methods avoid fake ranking. Ordinal categories have meaningful order, so ordered numeric mapping can be valid. "
                "High-cardinality categories can explode the feature space. Unseen production categories require an explicit route: unknown bucket, safe ignore, or contract violation."
            ),
            "worked_example_slow": (
                "If station_type is ['station', 'equipment', 'electrical_board'], assigning 1, 2, 3 makes the model think electrical_board is greater than station. That order is fake. "
                "One-hot encoding creates separate yes/no columns. If a new value arrives, the production pipeline must not invent a new live column; it should use the planned unknown strategy."
            ),
            "model_sensitivity": [
                "Linear and distance-based models can be strongly affected by fake numeric order.",
                "Tree models can handle ordinal-like splits but still suffer if the encoding injects misleading structure.",
                "Recommendation and high-cardinality systems often need hashing, target encoding with leakage controls, or embeddings rather than naive one-hot.",
            ],
            "mission_prep": _MLF013_MISSION_PREP,
        }
    )
    return base


_CUSTOM_BUILDERS = {
    "mlf_013": _mlf013,
    "mlf_014": _mlf014,
}


def build_tutor_narrative(topic_id: str, blueprint: Dict[str, Any]) -> Dict[str, Any]:
    """Convert a topic blueprint into a teacher-style lesson narrative.

    The blueprint is the source of truth. This renderer deliberately avoids
    dumping raw blueprint fields into the UI. It teaches in sequence: intuition,
    precise definition, mechanism, example, nuance, architecture, mission prep.
    """
    builder = _CUSTOM_BUILDERS.get(topic_id)
    if builder:
        return builder(blueprint)
    return _generic_narrative(topic_id, blueprint)
