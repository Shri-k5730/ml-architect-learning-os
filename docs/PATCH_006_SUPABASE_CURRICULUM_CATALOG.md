# Patch 006 . Supabase-native curriculum catalog

## Why this patch exists

Patch 005 added the checkpoint and Advanced ML block, but it still relied on `data/progress_tracker.csv` and local catalog files as the runtime source. That repeats the V1 weakness: when Streamlit sleeps or redeploys, local files can become stale or misleading.

Patch 006 makes Supabase the runtime source for curriculum and progress while keeping local files as a safe developer fallback.

## What changes

### New Supabase tables

Run `supabase/sql/006_curriculum_catalog.sql` once in Supabase SQL Editor.

It creates:

- `mlos_topic_catalog`
- `mlos_learner_progress`

It also seeds:

- `mlf_001` to `mlf_010`
- `checkpoint_ml_foundations_001`
- `mlf_011` to `mlf_020`

### New code module

`src/utils/curriculum_catalog.py`

Responsibilities:

- Read topic catalog from Supabase first.
- Fall back to `topics/topic_catalog.json` only when Supabase/table is unavailable.
- Seed Supabase catalog from local JSON only if the table exists and is empty.
- Normalize Supabase rows into the existing `Topic` schema.

### Updated modules

- `app.py`
- `src/start_lesson.py`
- `src/evaluate_lesson.py`
- `src/agents/topic_selector.py`
- `src/utils/cloud_state.py`
- `src/utils/tracker.py`
- `src/utils/supabase_store.py`

## Runtime behavior after this patch

On app startup:

1. App checks Supabase.
2. If `mlos_topic_catalog` exists but is empty, it seeds from local topic JSON.
3. It rebuilds progress from durable Supabase evaluation artifacts.
4. It writes repaired progress to:
   - `mlos_state.progress_tracker`
   - `mlos_learner_progress`
   - local CSV cache
5. UI renders from the repaired cache, which now reflects Supabase truth.

## Correct deployment sequence

1. Run SQL first:

```sql
-- Supabase SQL Editor
-- paste and run: supabase/sql/006_curriculum_catalog.sql
```

2. Deploy patch:

```bash
git checkout -b v2-supabase-curriculum
# unzip patch into repo root
python -m compileall app.py src
git add app.py src supabase docs
git commit -m "Move curriculum catalog and progress to Supabase"
git push
```

3. Open the app.

You should see a small caption near the top:

```text
Curriculum source: supabase:mlos_topic_catalog . topics: 21
```

If you see this instead:

```text
Curriculum source: local:topics/topic_catalog.json . topics: 21
```

then the app still works, but Supabase catalog is not active. Usually this means the SQL was not run, the table name is wrong, or Supabase credentials are not available in Streamlit secrets.

## What this patch does not do

It does not remove local topic files. They remain as seed/fallback files.

It does not make the app multi-user yet. `mlos_learner_progress` is single-user for now. Multi-user later should add `user_id` and use `(user_id, topic_id)` as the primary key.

It does not add the DL/NN block yet. That should happen after Advanced ML lessons 11 to 20 are stable.
