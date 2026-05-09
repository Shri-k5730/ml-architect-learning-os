# Patch 004: Fix Streamlit Code Lab timeout runner

## Problem

The Code Lab returned:

```text
signal only works in main thread of the main interpreter
```

This happened because `src/utils/code_runner.py` used `signal.alarm()` for timeouts. Streamlit button callbacks may run outside the main interpreter thread, where Python's `signal` module cannot install alarms.

## Fix

- Removed `signal` and `_time_limit()`.
- Added `_run_with_timeout()` using `ThreadPoolExecutor`.
- Preserved the existing `run_code_exercise(exercise, submission)` dictionary API.
- Added safe built-ins for `ValueError`, `TypeError`, and `Exception` so learner validation code does not fail unnecessarily.

## Learner note

For the current `mlf_009` exercise, empty lists are tested as a hidden case. The expected return is `0.0`, not an exception.

Use:

```python
def calculate_accuracy(y_true, y_pred):
    if len(y_true) != len(y_pred):
        raise ValueError("y_true and y_pred must have the same length")
    if len(y_true) == 0:
        return 0.0
    correct = 0
    for actual, predicted in zip(y_true, y_pred):
        if actual == predicted:
            correct += 1
    return correct / len(y_true)
```

## Apply

```bash
python -m compileall app.py src

git add src/utils/code_runner.py docs/PATCH_004_STREAMLIT_CODE_RUNNER_TIMEOUT.md
git commit -m "Fix Streamlit Code Lab timeout runner"
git push
```
