# Supabase export audit used for MLOS V4

The supplied exports were inspected before changing the architecture.

## Snapshot counts

- Runs: 66
- Artifacts: 692
- Learner progress rows: 52
- Active learning-policy rows supplied: 1
- Topic catalog rows: 52

## AIA_004 state in the supplied snapshot

- Previous evaluated run: `20260805_063411_aia_004`, `evaluation_complete`, `completed`
- Active repair run: `20260809_072249_aia_004`, `awaiting_user_answers`, `in_progress`
- Durable learner-progress row still records the previous borderline scores, including Practical = 2.

V4 deliberately does not rewrite those historical rows. The active repair can continue after deployment.

## Data migration policy

The V4 SQL migration updates only:

- active topic learning designs for `aia_001` through `aia_010`;
- the active learning-policy record;
- the version manifest.

It does not delete or rewrite prior runs, artifacts, rewards, events, or learner-progress history.
