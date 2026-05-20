-- Patch 036 diagnostics only. No data mutation.

-- 1. Completed-only Review/Redo visibility check.
select
  t.topic_id,
  t.sequence_no,
  t.title,
  coalesce(lp.status, 'missing_progress') as progress_status,
  coalesce(lp.attempt_count, 0) as attempt_count,
  count(r.run_id) as total_runs,
  count(*) filter (where r.status = 'completed') as completed_runs,
  max(r.created_at) as latest_run_at
from public.mlos_topic_catalog t
left join public.mlos_learner_progress lp
  on lp.topic_id = t.topic_id
left join public.mlos_runs r
  on r.topic_id = t.topic_id
group by
  t.topic_id,
  t.sequence_no,
  t.title,
  lp.status,
  lp.attempt_count
order by t.sequence_no asc;

-- 2. Active awaiting runs. Intentional redo should show redo_mode=true or selection_mode=retry.
select
  run_id,
  topic_id,
  topic_title,
  phase,
  status,
  run_state->>'selection_mode' as selection_mode,
  run_state->>'redo_mode' as redo_mode,
  created_at,
  updated_at
from public.mlos_runs
where phase = 'awaiting_user_answers'
order by created_at desc
limit 20;

-- 3. Verify Draft vs Final Evaluation artifacts for recent problem topics.
select
  r.run_id,
  r.topic_id,
  r.phase,
  r.status,
  a.artifact_type,
  a.created_at,
  a.payload
from public.mlos_runs r
join public.mlos_artifacts a
  on a.run_id = r.run_id
where r.topic_id in ('mlf_018', 'mlf_019')
  and a.artifact_type in ('answers', 'draft_verification', 'evaluation', 'answer_coaching')
order by r.created_at desc, a.created_at asc;

-- 4. Code Lab persistence check.
select
  run_id,
  topic_id,
  artifact_type,
  created_at
from public.mlos_artifacts
where artifact_type in ('practice_exercise', 'practice_submission_template', 'practice_submission', 'practice_result', 'practice_coaching')
order by created_at desc
limit 50;
