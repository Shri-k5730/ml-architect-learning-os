from __future__ import annotations

import ast
import math
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from typing import Any, Callable, Dict, List, Optional, Tuple


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
    "sorted": sorted,
    "set": set,
    "sum": sum,
    "tuple": tuple,
    "zip": zip,
    "ValueError": ValueError,
    "TypeError": TypeError,
    "Exception": Exception,
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


def _run_with_timeout(func: Callable[[], Any], timeout_seconds: int) -> Any:
    """Run a small restricted callable with a timeout that works in Streamlit threads.

    Python's signal.alarm only works in the main interpreter thread. Streamlit can
    execute button callbacks outside that thread, so signal-based timeouts fail
    with: "signal only works in main thread of the main interpreter".

    This uses a worker thread instead. It is designed for tiny educational
    exercises, not arbitrary untrusted long-running programs.
    """
    timeout_seconds = max(1, int(timeout_seconds or 2))
    executor = ThreadPoolExecutor(max_workers=1)
    future = executor.submit(func)
    try:
        return future.result(timeout=timeout_seconds)
    except FutureTimeoutError as exc:
        future.cancel()
        raise TimeoutError("Code execution timed out.") from exc
    finally:
        executor.shutdown(wait=False, cancel_futures=True)


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

    def _compile_and_exec() -> None:
        exec(compile(source, "<practice_submission>", "exec"), namespace, namespace)

    _run_with_timeout(_compile_and_exec, timeout_seconds)

    fn = namespace.get(function_name)
    if not callable(fn):
        raise CodeRunnerError(f"Expected a callable function named '{function_name}'.")
    return fn


def _is_expected(actual: Any, expected: Any) -> bool:
    """Compare test outputs with float tolerance and nested structure support."""
    if isinstance(expected, dict):
        if not isinstance(actual, dict):
            return False
        if set(actual.keys()) != set(expected.keys()):
            return False
        return all(_is_expected(actual[key], expected[key]) for key in expected.keys())

    if isinstance(expected, (list, tuple)):
        if not isinstance(actual, (list, tuple)):
            return False
        if len(actual) != len(expected):
            return False
        return all(_is_expected(a, e) for a, e in zip(actual, expected))

    if isinstance(expected, float) or isinstance(actual, float):
        try:
            return math.isclose(float(actual), float(expected), rel_tol=1e-9, abs_tol=1e-9)
        except Exception:
            return False
    return actual == expected


def _safe_error_category(error: str) -> str:
    lowered = (error or "").lower()
    if "division by zero" in lowered or "zero" in lowered:
        return "zero_denominator_or_empty_input"
    if "name" in lowered and "not defined" in lowered:
        return "undefined_name_or_typo"
    if "timed out" in lowered:
        return "timeout"
    if "syntax" in lowered:
        return "syntax"
    if "expected" in lowered:
        return "incorrect_output"
    if error:
        return "runtime_error"
    return "incorrect_output"


def _run_one_test(fn: Any, test: Dict[str, Any], timeout_seconds: int) -> Dict[str, Any]:
    args = test.get("args", [])
    kwargs = test.get("kwargs", {})
    expected = test.get("expected")
    expected_error = str(test.get("expected_error") or "").strip()

    if not isinstance(args, list):
        args = [args]
    if not isinstance(kwargs, dict):
        kwargs = {}

    try:
        actual = _run_with_timeout(lambda: fn(*args, **kwargs), timeout_seconds)
        if expected_error:
            passed = False
            error = f"Expected {expected_error} to be raised, got output {actual!r}."
        else:
            passed = _is_expected(actual, expected)
            error = "" if passed else f"Expected {expected!r}, got {actual!r}."
    except Exception as exc:
        actual = None
        if expected_error and exc.__class__.__name__ == expected_error:
            passed = True
            error = ""
        else:
            passed = False
            error = str(exc)

    failure_category = test.get("concept_tag") or _safe_error_category(error)

    return {
        "name": test.get("name", "unnamed_test"),
        "passed": passed,
        "expected": expected_error or expected,
        "actual": actual,
        "error": error,
        "reason": test.get("reason", ""),
        "scenario": test.get("scenario") or test.get("reason", ""),
        "concept_tag": test.get("concept_tag", failure_category),
        "failure_category": failure_category,
        "failure_hint": test.get("failure_hint", "Re-check the formula and edge cases for this scenario."),
        "visibility": test.get("visibility", "visible"),
        "show_inputs": bool(test.get("show_inputs", False)),
        "show_expected": bool(test.get("show_expected", True)),
        "show_actual": bool(test.get("show_actual", True)),
        "args": args if test.get("show_inputs", False) else None,
        "kwargs": kwargs if test.get("show_inputs", False) else None,
    }


def _sanitize_hidden_test_result(item: Dict[str, Any], ordinal: int) -> Dict[str, Any]:
    """Keep hidden tests useful without leaking the test data or expected output."""
    return {
        "name": f"hidden_test_{ordinal}",
        "passed": bool(item.get("passed")),
        "failure_category": item.get("failure_category") or item.get("concept_tag") or "hidden_case",
        "concept_tag": item.get("concept_tag") or item.get("failure_category") or "hidden_case",
        "failure_hint": item.get("failure_hint") or "Review the edge case named by the failure category.",
        "scenario": item.get("scenario", "Hidden diagnostic case"),
        "visibility": "hidden",
    }


def _diagnostics_from_results(visible_results: List[Dict[str, Any]], hidden_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    failed_visible = [item for item in visible_results if not item.get("passed")]
    failed_hidden = [item for item in hidden_results if not item.get("passed")]

    failed_categories: List[str] = []
    hints: List[str] = []

    for item in failed_visible + failed_hidden:
        category = str(item.get("failure_category") or item.get("concept_tag") or "unknown")
        if category not in failed_categories:
            failed_categories.append(category)
        hint = str(item.get("failure_hint") or "")
        if hint and hint not in hints:
            hints.append(hint)

    return {
        "failed_visible_count": len(failed_visible),
        "failed_hidden_count": len(failed_hidden),
        "failed_categories": failed_categories,
        "hints": hints,
    }


def _interpretation_score(
    interpretation: str,
    expected_focus: List[str],
    configured_groups: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    text = (interpretation or "").strip()
    lowered = text.lower()
    hits: List[str] = []
    missing: List[str] = []

    default_groups: List[Tuple[str, List[str]]] = [
        ("minority/positive cases", ["minority", "positive", "rare", "imbalance", "imbalanced", "defect", "defective", "failure"]),
        ("business cost", ["business", "cost", "risk", "impact", "expensive", "warranty", "rework", "quality", "go-live"]),
        ("error type", ["false negative", "false positive", "missed", "wrong", "false alarm", "miss"]),
        ("better metrics", ["precision", "recall", "confusion", "f1", "class-specific", "class specific"]),
        ("production decision", ["production", "threshold", "monitor", "decision", "alert", "deploy", "deployment", "owner", "response"]),
    ]
    keyword_groups = default_groups
    if configured_groups:
        parsed_groups: List[Tuple[str, List[str]]] = []
        for group in configured_groups:
            if not isinstance(group, dict):
                continue
            label = str(group.get("label") or "").strip()
            keywords = [str(item).lower() for item in (group.get("keywords") or []) if str(item).strip()]
            if label and keywords:
                parsed_groups.append((label, keywords))
        if parsed_groups:
            keyword_groups = parsed_groups

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
    function_names = sorted(
        {
            str(test.get("function_name") or function_name)
            for test in (exercise.get("visible_tests", []) + exercise.get("hidden_tests", []))
            if str(test.get("function_name") or function_name).strip()
        }
    )

    result: Dict[str, Any] = {
        "topic_id": exercise.get("topic_id"),
        "exercise_id": exercise.get("exercise_id"),
        "title": exercise.get("title"),
        "status": "not_run",
        "function_name": function_name,
        "function_names": function_names or [function_name],
        "visible_tests": [],
        "hidden_tests": [],
        "diagnostics": {
            "failed_visible_count": 0,
            "failed_hidden_count": 0,
            "failed_categories": [],
            "hints": [],
        },
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
        loaded_functions = {
            name: _load_function(code, function_name=name, timeout_seconds=timeout_seconds)
            for name in (function_names or [function_name])
        }
        visible_results = [
            _run_one_test(
                loaded_functions[str(test.get("function_name") or function_name)],
                test | {"visibility": "visible"},
                timeout_seconds,
            )
            for test in exercise.get("visible_tests", [])
        ]
        raw_hidden_results = [
            _run_one_test(
                loaded_functions[str(test.get("function_name") or function_name)],
                test | {"visibility": "hidden", "show_expected": False, "show_actual": False, "show_inputs": False},
                timeout_seconds,
            )
            for test in exercise.get("hidden_tests", [])
        ]
        hidden_results = [
            _sanitize_hidden_test_result(item, ordinal=index + 1)
            for index, item in enumerate(raw_hidden_results)
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
        result["diagnostics"] = {
            "failed_visible_count": len(exercise.get("visible_tests", [])),
            "failed_hidden_count": len(exercise.get("hidden_tests", [])),
            "failed_categories": [_safe_error_category(str(exc))],
            "hints": ["Fix the runtime error before debugging metric logic."],
        }
        result["interpretation"] = _interpretation_score(
            interpretation,
            exercise.get("expected_interpretation_focus", []),
            exercise.get("interpretation_keyword_groups"),
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
    result["diagnostics"] = _diagnostics_from_results(visible_results, hidden_results)
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
        exercise.get("interpretation_keyword_groups"),
    ) | {"text": interpretation}
    result["status"] = "passed" if passed else "failed"
    return result


def build_practice_coaching(exercise: Dict[str, Any], result: Dict[str, Any]) -> Dict[str, Any]:
    summary = result.get("summary", {})
    interpretation = result.get("interpretation", {})
    diagnostics = result.get("diagnostics", {}) or {}
    passed = bool(summary.get("passed"))
    missing_focus = interpretation.get("missing_focus", []) or []
    failed_categories = diagnostics.get("failed_categories", []) or []
    diagnostic_hints = diagnostics.get("hints", []) or []

    if passed and not missing_focus:
        next_step = "Good. Now connect the metric result to the production decision and threshold policy."
    elif passed:
        next_step = "The code is correct. Strengthen the interpretation by naming business cost, error type, and the metric you would add."
    else:
        next_step = "Fix the function first. Use the failed skill categories below before looking at any sample answer."

    default_better_code = """def calculate_accuracy(y_true, y_pred):\n    if not y_true:\n        return 0.0\n    correct = sum(1 for actual, predicted in zip(y_true, y_pred) if actual == predicted)\n    return correct / len(y_true)\n"""
    default_better_interpretation = (
        "The 0.8 accuracy looks good, but the model missed the only positive case. "
        "In production, that could be the exact case the business cares about, such as a defect, fraud, or failure risk. "
        "I would inspect the confusion matrix and add recall/precision for the positive class before trusting the model. "
        "The metric should match the cost of false negatives and false positives."
    )

    return {
        "topic_id": exercise.get("topic_id"),
        "exercise_id": exercise.get("exercise_id"),
        "title": exercise.get("title"),
        "passed": passed,
        "test_summary": summary,
        "diagnostics": diagnostics,
        "failed_categories": failed_categories,
        "diagnostic_hints": diagnostic_hints,
        "interpretation_score": interpretation.get("score", 1),
        "missing_interpretation_focus": missing_focus,
        "better_code": exercise.get("better_code") or default_better_code,
        "better_interpretation": exercise.get("better_interpretation") or default_better_interpretation,
        "next_step": next_step,
    }
