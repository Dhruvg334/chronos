-- Durable first-run state, explicit planning preferences, and concise recommendation feedback.

ALTER TABLE public.user_profiles
    ADD COLUMN onboarding_status TEXT NOT NULL DEFAULT 'not_started'
        CHECK (onboarding_status IN ('not_started','in_progress','completed','skipped')),
    ADD COLUMN onboarding_step SMALLINT NOT NULL DEFAULT 1 CHECK (onboarding_step BETWEEN 1 AND 3),
    ADD COLUMN onboarding_completed_at TIMESTAMPTZ,
    ADD COLUMN planning_style TEXT NOT NULL DEFAULT 'balanced'
        CHECK (planning_style IN ('guided','balanced','minimal')),
    ADD COLUMN recommendation_frequency TEXT NOT NULL DEFAULT 'normal'
        CHECK (recommendation_frequency IN ('low','normal','high')),
    ADD COLUMN approval_strictness TEXT NOT NULL DEFAULT 'always_ask'
        CHECK (approval_strictness IN ('always_ask','allow_reversible')),
    ADD COLUMN internal_write_automation_enabled BOOLEAN NOT NULL DEFAULT FALSE,
    ADD COLUMN preferred_focus_durations SMALLINT[] NOT NULL DEFAULT ARRAY[25,45,60]::SMALLINT[]
        CHECK (cardinality(preferred_focus_durations) BETWEEN 1 AND 5 AND preferred_focus_durations <@ ARRAY[15,20,25,30,45,60,90,120,180]::SMALLINT[]),
    ADD COLUMN routine_continuity_preference TEXT NOT NULL DEFAULT 'gentle'
        CHECK (routine_continuity_preference IN ('gentle','standard','structured')),
    ADD COLUMN quick_task_mode TEXT NOT NULL DEFAULT 'batch'
        CHECK (quick_task_mode IN ('immediate','batch')),
    ADD COLUMN strategy_preferences TEXT[] NOT NULL DEFAULT ARRAY['eisenhower_triage','task_batching','continuity_recovery','focus_interval','constrained_day','quick_action','time_blocking']::TEXT[],
    ADD COLUMN explanation_detail TEXT NOT NULL DEFAULT 'standard'
        CHECK (explanation_detail IN ('brief','standard','detailed'));

CREATE TABLE public.recommendation_feedback (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.user_profiles(id) ON DELETE CASCADE,
    recommendation_type TEXT NOT NULL CHECK (length(recommendation_type) BETWEEN 1 AND 80),
    recommendation_key TEXT CHECK (recommendation_key IS NULL OR length(recommendation_key) <= 160),
    context_summary JSONB NOT NULL DEFAULT '{}'::JSONB,
    user_action TEXT NOT NULL CHECK (user_action IN ('useful','not_useful','used','dismissed','edited_before_use','postponed')),
    reason_category TEXT CHECK (reason_category IS NULL OR reason_category IN ('not_relevant','bad_timing','too_much_effort','already_handled','other')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc', now()),
    CHECK (pg_column_size(context_summary) <= 4096)
);

CREATE INDEX recommendation_feedback_user_created_idx ON public.recommendation_feedback(user_id, created_at DESC);
ALTER TABLE public.recommendation_feedback ENABLE ROW LEVEL SECURITY;
CREATE POLICY recommendation_feedback_owner_all ON public.recommendation_feedback
    FOR ALL USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);

REVOKE ALL ON public.recommendation_feedback FROM PUBLIC, anon;
GRANT SELECT, INSERT ON public.recommendation_feedback TO authenticated, service_role;

COMMENT ON COLUMN public.recommendation_feedback.context_summary IS 'Concise deterministic context only; never raw prompts, responses, or hidden reasoning.';
