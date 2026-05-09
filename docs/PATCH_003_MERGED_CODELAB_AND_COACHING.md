# Patch 003 . Merge Code Lab and Draft Coaching

This patch replaces Patch 002 as the safe application package. It preserves the practical Code Lab introduced in Patch 001 and adds the copy-safe Verify Draft and topic-grounded coaching from Patch 002.

## Why this exists
Patch 002 overwrote `app.py` from Patch 001 and removed the Code Lab UI path. This patch merges both feature paths instead of treating them as independent replacements.

## Preserved from Patch 001
- `mlf_009` deterministic coding exercise.
- Code Lab UI in Current Level.
- `practice_exercise`, `practice_submission`, `practice_result`, and `practice_coaching` artifacts.
- Practical scoring gate in evaluation.

## Added from Patch 002
- Verify Draft before final evaluation.
- Copy-safe guidance with no polished answers before final submission.
- Collapsed stronger sample answers after final evaluation.
- Topic-grounded coaching profiles for `mlf_008` and `mlf_009`.
- Evidence-bound coaching findings.

## Apply
```bash
python -m compileall app.py src
git add app.py src docs
git commit -m "Merge Code Lab with draft verification coaching"
git push
```

## Test
Start a fresh `mlf_009` run and verify:
1. Written missions are visible.
2. Code Lab is visible.
3. Run Code Exercise works.
4. Verify Draft works and shows hints only.
5. Save + Evaluate runs both written and practical checks.
