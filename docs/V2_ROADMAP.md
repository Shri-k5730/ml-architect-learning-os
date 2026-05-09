# ML Architect Learning OS V2 Roadmap

## V2 objective

Move the OS from written ML explanation practice to applied ML Architect training. The learner should explain, calculate, code, diagnose, and make architecture decisions.

## V2 principles

1. Written answers alone are not enough.
2. Each 10-lesson block must end with a checkpoint before the next block unlocks.
3. Coding exercises must be deterministic and test-backed, not invented during evaluation.
4. LLM evaluation can judge reasoning, but code correctness must be verified by tests.
5. The next content layer should move from ML foundations to neural-network foundations, not transformers yet.

## Phase 1 . Practical code lab foundation

Implemented first for `mlf_009`.

- Add `practice_exercise` artifact at lesson start.
- Add `practice_submission` artifact for learner code and interpretation.
- Run deterministic tests during evaluation.
- Persist `practice_result` and `practice_coaching`.
- Apply a practical gate so failed code cannot pass the lesson.

## Phase 2 . 10-lesson checkpoint

After `mlf_010`, create `checkpoint_ml_foundations_001`.

The checkpoint should test:

- concept synthesis across lessons 1-10
- metric interpretation
- leakage/generalization/baseline failure diagnosis
- small coding exercise
- architect controls: validation, monitoring, fallback, and retraining

Unlock rule:

- pass: unlock `mlf_011`
- borderline: retry targeted weak areas or unlock only with weakness log
- revise: retry checkpoint
- fail prerequisite: route back to specific weak lesson

## Phase 3 . V2 lesson block: neural-network foundations

Recommended next 10 lessons:

| ID | Topic | Practical exercise |
|---|---|---|
| mlf_011 | From linear model to artificial neuron | Implement weighted sum `z = w·x + b` |
| mlf_012 | Activation functions: sigmoid, tanh, ReLU | Implement sigmoid/ReLU and explain saturation |
| mlf_013 | Forward pass and tensor shapes | Compute layer output shapes |
| mlf_014 | Loss functions in neural networks | Implement MSE/BCE on tiny arrays |
| mlf_015 | Gradient descent intuition | Perform one manual weight update |
| mlf_016 | Backpropagation without the math panic | Trace which parameter changed loss |
| mlf_017 | Epochs, batches, and training loops | Write a tiny batch loop |
| mlf_018 | Overfitting in neural networks | Interpret train/validation loss curves |
| mlf_019 | Vanishing/exploding gradients | Diagnose unstable training logs |
| mlf_020 | Neural network deployment readiness | Define monitoring, fallback, and drift controls |

## Phase 4 . Scoring upgrade

Add a fifth scoring dimension:

- coding_correctness

Recommended V2 scoring:

- conceptual_clarity: 1-5
- practical_reasoning: 1-5
- coding_correctness: 1-5
- architect_reasoning: 1-5
- communication: 1-5

Initial pass rule:

- total >= 18/25
- coding_correctness >= 3
- architect_reasoning >= 3

## Phase 5 . UI upgrade

Add these tabs or panels:

- Code Lab
- Practical Result
- Checkpoint Readiness
- Weakness Replay
- V2 Roadmap

## Build order

1. Finish practical code lab for `mlf_009`.
2. Add code exercises for `mlf_010` and `mlf_011`.
3. Add checkpoint object and checkpoint selector.
4. Add topics `mlf_011` to `mlf_020` behind the checkpoint gate.
5. Add fifth scoring dimension.
6. Add weak-area replay loop.
