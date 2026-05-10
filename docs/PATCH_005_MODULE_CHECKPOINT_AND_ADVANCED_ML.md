# Patch 005 . Module Checkpoint and Advanced ML Block

## Purpose

This patch adds the first module gate after the 10 ML foundation lessons and appends the next 10-topic Advanced ML block.

The new progression is:

1. `mlf_001` to `mlf_010` . ML Foundations
2. `checkpoint_ml_foundations_001` . ML Foundations Review
3. `mlf_011` to `mlf_020` . Advanced ML

The checkpoint must be completed before `mlf_011` unlocks.

## What changed

### New checkpoint

Added a deterministic checkpoint topic:

- `checkpoint_ml_foundations_001` . Checkpoint 1: ML Foundations Review

This is not a normal lesson. It uses static checkpoint content and assessment missions so the review stays stable and does not drift with LLM generation.

Checkpoint assessment covers:

- baseline
- train/test split
- generalization
- data leakage
- accuracy
- precision vs recall
- production go-live checklist

### New Code Lab for checkpoint

The checkpoint includes a practical coding exercise:

```python
def calculate_precision_recall(y_true, y_pred, positive_label=1):
    ...
```

Expected output format:

```python
{"precision": 0.6, "recall": 0.3}
```

The Code Lab now supports nested expected outputs such as dictionaries and lists with float tolerance.

### New Advanced ML lessons

Added:

- `mlf_011` . Model selection and validation strategy
- `mlf_012` . Feature engineering and feature contracts
- `mlf_013` . Encoding categorical variables safely
- `mlf_014` . Scaling, normalization, and pipeline leakage
- `mlf_015` . Regularization: controlling model complexity
- `mlf_016` . Threshold tuning and cost-sensitive decisions
- `mlf_017` . Class imbalance handling strategies
- `mlf_018` . Error analysis and model debugging
- `mlf_019` . Model interpretability and explainability limits
- `mlf_020` . ML monitoring: drift, performance, and retraining triggers

Deep Learning and Neural Networks are intentionally not added yet. They should become the next block after Advanced ML.

## Files changed

```text
data/progress_tracker.csv
topics/topic_catalog.json
topics/topic_unlock_rules.json
src/start_lesson.py
src/checkpoints/__init__.py
src/checkpoints/checkpoint_bank.py
src/practice/exercise_bank.py
src/utils/code_runner.py
src/agents/topic_coaching_profiles.py
docs/PATCH_005_MODULE_CHECKPOINT_AND_ADVANCED_ML.md
```

## Apply

```bash
python -m compileall app.py src

git add data/progress_tracker.csv topics src docs
git commit -m "Add ML foundations checkpoint and advanced ML block"
git push
```

## Test

After `mlf_010` is completed, `checkpoint_ml_foundations_001` should unlock. After the checkpoint is completed, `mlf_011` should unlock.

The checkpoint should show:

- Current Level content marked as a checkpoint/review
- five written missions
- Code Lab for precision/recall
- normal Verify Draft
- Save + Evaluate with Code Lab gate
