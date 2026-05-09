from __future__ import annotations

import ast
import math
import signal
from contextlib import contextmanager
from typing import Any, Dict, List, Optional, Tuple


class CodeRunnerError(Exception):
    """Raised when a practice code exercise cannot be evaluated."""


SAFE_BUILTINS = {
    "abs": abs,
    "all": all,
    "any": any,
    "bool": bool,
    "dict": dict,
    "enumerate": enumerate,
    "float": float,
    "int": int,
    "len": len,
    "list": list,
    "max": max,
    "min": min,
    "range": range,
    "round": round,
    "sum": sum,
    "tuple": tuple,
    "zip": zip,
}

BLOCKED_NAMES = {
    "__import__",
    "breakpoint",
    "compile",
    "delattr",
    "dir",
    "eval",
    "exec",
    "exit",
    "getattr",
    "globals",
    "help",
    "input",
    "locals",
    "open",
    "print",
    "quit",
    "setattr",
    "vars",
}

BLOCKED_MODULES = {
    "builtins",
    "ctypes",
    "importlib",
    "inspect",
    "io",
    "multiprocessing",
    "os",
    "pathlib",
    "pickle",
    "platform",
    "shutil",
    "signal",
    "socket",
    "subprocess",
    "sys",
    "threading",
}


@contextmanager
def _time_limit(seconds: int):
    # Streamlit Cloud/Linux supports SIGALRM. Windows local development does not.
    # On Windows we still run the AST-restricted code path, but skip the alarm.
    if not hasattr(signal, "SIGALRM"):
        yield
        return

    def _handler(signum, frame):  # pragma: no cover - signal callback
        raise TimeoutError("Code execution timed out.")

    previous = signal.signal(signal.SIGALRM, _handler)
    signal.alarm(max(1, int(seconds)))
    try:
        yield
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, previous)


def _validate_source(source: str) -> None:
    if not isinstance(source, str) or not source.strip():
        raise CodeRunnerError("Code submission is empty.")

    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        raise CodeRunnerError(f"Syntax error: {exc.msg} at line {exc.lineno}.") from exc

    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            raise CodeRunnerError("Imports are disabled for this exercise.")

        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name) and func.id in BLOCKED_NAMES:
                raise CodeRunnerError(f"Use of '{func.id}' is not allowed in this exercise.")
            if isinstance(func, ast.Attribute) and func.attr.startswith("__"):
                raise CodeRunnerError("Dunder attribute calls are not allowed.")

        if isinstance(node, ast.Name):
            if node.id in BLOCKED_MODULES or node.id in BLOCKED_NAMES:
                raise CodeRunnerError(f"Use of '{node.id}' is not allowed in this exercise.")
            if node.id.startswith("__"):
                raise CodeRunnerError("Dunder names are not allowed.")

        if isinstance(node, ast.Attribute):
            if node.attr.startswith("__"):
                raise CodeRunnerError("Dunder attributes are not allowed.")


def _load_function(source: str, function_name: str, timeout_seconds: int) -> Any:
    _validate_source(source)
    namespace: Dict[str, Any] = {"__builtins__": SAFE_BUILTINS}

    with _time_limit(timeout_seconds):
        exec(compile(source, "<practice_submission>", "exec"), namespace, namespace)

    fn = namespace.get(function_name)
    if not callable(fn):
        raise CodeRunnerError(f"Expected a callable function named '{function_name}'.")
    return fn


def _is_expected(actual: Any, expected: Any) -> bool:
    if isinstance(expected, float) or isinstance(actual, float):
        try:
            return math.isclose(float(actual), float(expected), rel_tol=1e-9, abs_tol=1e-9)
        except Exception:
            return False
    return actual == expected


def _run_one_test(fn: Any, test: Dict[str, Any], timeout_seconds: int) -> Dict[str, Any]:
    args = test.get("args", [])
    kwargs = test.get("kwargs", {})
    expected = test.get("expected")

    if not isinstance(args, list):
        args = [args]
    if not isinstance(kwargs, dict):
        kwargs = {}

    try:
        with _time_limit(timeout_seconds):
            actual = fn(*args, **kwargs)
        passed = _is_expected(actual, expected)
        error = "" if passed else f"Expected {expected!r}, got {actual!r}."
    except Exception as exc:
        actual = None
        passed = False
        error = str(exc)

    return {
        "name": test.get("name", "unnamed_test"),
        "passed": passed,
        "expected": expected,
        "actual": actual,
        "error": error,
        "reason": test.get("reason", ""),
    }


def _interpretation_score(interpretation: str, expected_focus: List[str]) -> Dict[str, Any]:
    text = (interpretation or "").strip()
    lowered = text.lower()
    hits: List[str] = []
    missing: List[str] = []

    keyword_groups: List[Tuple[str, List[str]]] = [
        ("minority/positive cases", ["minority", "positive", "rare", "imbalance", "imbalanced"]),
        ("business cost", ["business", "cost", "risk", "impact", "expensive"]),
        ("error type", ["false negative", "false positive", "missed", "wrong"]),
        ("better metrics", ["precision", "recall", "confusion", "f1", "class-specific", "class specific"]),
        ("production decision", ["production", "threshold", "monitor", "decision", "alert"]),
    ]

    for label, keywords in keyword_groups:
        if any(keyword in lowered for keyword in keywords):
            hits.append(label)
        else:
            missing.append(label)

    score = max(1, min(5, len(hits)))
    if len(text) < 80:
        score = min(score, 2)
        if "specific interpretation length/depth" not in missing:
            missing.append("specific interpretation length/depth")

    return {
        "score": score,
        "matched_focus": hits,
        "missing_focus": missing,
        "expected_focus": expected_focus,
    }


def run_code_exercise(exercise: Dict[str, Any], submission: Dict[str, Any]) -> Dict[str, Any]:
    code = submission.get("code", "")
    interpretation = submission.get("interpretation", "")
    timeout_seconds = int(exercise.get("timeout_seconds", 2) or 2)
    function_name = exercise.get("function_name", "")

    result: Dict[str, Any] = {
        "topic_id": exercise.get("topic_id"),
        "exercise_id": exercise.get("exercise_id"),
        "title": exercise.get("title"),
        "status": "not_run",
        "function_name": function_name,
        "visible_tests": [],
        "hidden_tests": [],
        "summary": {},
        "interpretation": {
            "text": interpretation,
            "score": 1,
            "matched_focus": [],
            "missing_focus": [],
            "expected_focus": exercise.get("expected_interpretation_focus", []),
        },
        "error": "",
    }

    try:
        fn = _load_function(code, function_name=function_name, timeout_seconds=timeout_seconds)
        visible_results = [
            _run_one_test(fn, test, timeout_seconds)
            for test in exercise.get("visible_tests", [])
        ]
        hidden_results = [
            _run_one_test(fn, test, timeout_seconds)
            for test in exercise.get("hidden_tests", [])
        ]
    except Exception as exc:
        result["status"] = "error"
        result["error"] = str(exc)
        result["summary"] = {
            "passed": False,
            "visible_passed": 0,
            "visible_total": len(exercise.get("visible_tests", [])),
            "hidden_passed": 0,
            "hidden_total": len(exercise.get("hidden_tests", [])),
            "total_passed": 0,
            "total_tests": len(exercise.get("visible_tests", [])) + len(exercise.get("hidden_tests", [])),
        }
        result["interpretation"] = _interpretation_score(
            interpretation,
            exercise.get("expected_interpretation_focus", []),
        ) | {"text": interpretation}
        return result

    visible_passed = sum(1 for item in visible_results if item["passed"])
    hidden_passed = sum(1 for item in hidden_results if item["passed"])
    visible_total = len(visible_results)
    hidden_total = len(hidden_results)
    total_passed = visible_passed + hidden_passed
    total_tests = visible_total + hidden_total
    passed = total_tests > 0 and total_passed == total_tests

    result["visible_tests"] = visible_results
    result["hidden_tests"] = hidden_results
    result["summary"] = {
        "passed": passed,
        "visible_passed": visible_passed,
        "visible_total": visible_total,
        "hidden_passed": hidden_passed,
        "hidden_total": hidden_total,
        "total_passed": total_passed,
        "total_tests": total_tests,
    }
    result["interpretation"] = _interpretation_score(
        interpretation,
        exercise.get("expected_interpretation_focus", []),
    ) | {"text": interpretation}
    result["status"] = "passed" if passed else "failed"
    return result


def build_practice_coaching(exercise: Dict[str, Any], result: Dict[str, Any]) -> Dict[str, Any]:
    summary = result.get("summary", {})
    interpretation = result.get("interpretation", {})
    passed = bool(summary.get("passed"))
    missing_focus = interpretation.get("missing_focus", []) or []

    if passed and not missing_focus:
        next_step = "Good. Now connect this metric to precision/recall trade-offs in the next lesson."
    elif passed:
        next_step = "The code is correct. Strengthen the interpretation by naming business cost, error type, and the metric you would add."
    else:
        next_step = "Fix the function first. Count matching label/prediction positions, divide by number of examples, and return 0.0 for empty input."

    return {
        "topic_id": exercise.get("topic_id"),
        "exercise_id": exercise.get("exercise_id"),
        "title": exercise.get("title"),
        "passed": passed,
        "test_summary": summary,
        "interpretation_score": interpretation.get("score", 1),
        "missing_interpretation_focus": missing_focus,
        "better_code": """def calculate_accuracy(y_true, y_pred):\n    if not y_true:\n        return 0.0\n    correct = sum(1 for actual, predicted in zip(y_true, y_pred) if actual == predicted)\n    return correct / len(y_true)\n""",
        "better_interpretation": (
            "The 0.8 accuracy looks good, but the model missed the only positive case. "
            "In production, that could be the exact case the business cares about, such as a defect, fraud, or failure risk. "
            "I would inspect the confusion matrix and add recall/precision for the positive class before trusting the model. "
            "The metric should match the cost of false negatives and false positives."
        ),
        "next_step": next_step,
    }
