# MLOS V2.3.2 . Changed Files Only

Extract this ZIP at the GitHub repo root. It contains only files that need to be added or overwritten.

## Deploy order

1. Extract at repo root.
2. Commit and push to GitHub.
3. Let Streamlit Cloud redeploy.
4. Run `supabase/sql/v2_3_mastery_tutor_fix/99_RUN_ALL_IN_ORDER.sql` in Supabase.
5. Refresh the app.

## Main rule

Use best mastered score, not latest failed redo, for progression.

- `best_stars >= 3` means mastered.
- `best_stars < 3` means repair required.
- A failed redo does not erase a previously mastered topic.

## Current repair queue from the latest export

Repair these ML lessons because best_stars is below 3:

- `mlf_009` . Why accuracy can lie
- `mlf_010` . Precision vs recall
- `mlf_012` . Feature engineering and feature contracts
- `mlf_014` . Scaling, normalization, and pipeline leakage
- `mlf_022` . Hyperparameter tuning without fooling yourself
- `mlf_023` . ROC, PR curves, and operating points
- `mlf_025` . Data quality, label quality, and sampling bias

Do not repair topics that already have at least one 3-star mastered attempt unless you voluntarily want a higher score.

## V2.3.2 specific fix

The previous V2.3.1 still allowed a stale local active run such as `mlf_016` to hijack the Current Level screen even when durable progress marked it mastered. V2.3.2 treats active runs for mastered topics as stale and ignores them.
