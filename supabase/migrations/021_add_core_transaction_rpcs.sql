-- Migration: 021_add_core_transaction_rpcs.sql
-- Description: Atomic, idempotent core-journey writes with ownership enforcement.

CREATE TABLE public.operation_receipts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.user_profiles(id) ON DELETE CASCADE,
    operation_type TEXT NOT NULL,
    idempotency_key TEXT NOT NULL CHECK (length(idempotency_key) BETWEEN 8 AND 200),
    result_json JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (user_id, operation_type, idempotency_key)
);

ALTER TABLE public.operation_receipts ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can read their own operation receipts"
    ON public.operation_receipts FOR SELECT USING (auth.uid() = user_id);

REVOKE ALL ON public.operation_receipts FROM PUBLIC, anon;
GRANT SELECT ON public.operation_receipts TO authenticated;
GRANT ALL ON public.operation_receipts TO service_role;

CREATE OR REPLACE FUNCTION public.approve_intake_transaction(
    p_user_id UUID,
    p_run_id UUID,
    p_idempotency_key TEXT,
    p_items JSONB
) RETURNS JSONB
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, public
AS $$
DECLARE
    v_item JSONB;
    v_task JSONB;
    v_result JSONB;
    v_ids JSONB := '[]'::JSONB;
BEGIN
    IF COALESCE(auth.role(), '') <> 'service_role' AND auth.uid() IS DISTINCT FROM p_user_id THEN
        RAISE EXCEPTION 'ownership validation failed' USING ERRCODE = '42501';
    END IF;
    IF p_idempotency_key IS NULL OR length(p_idempotency_key) < 8 THEN
        RAISE EXCEPTION 'invalid idempotency key' USING ERRCODE = '22023';
    END IF;
    PERFORM pg_advisory_xact_lock(hashtextextended(p_user_id::TEXT || ':intake:' || p_idempotency_key, 0));
    SELECT result_json INTO v_result FROM public.operation_receipts
      WHERE user_id = p_user_id AND operation_type = 'intake_approval' AND idempotency_key = p_idempotency_key;
    IF v_result IS NOT NULL THEN RETURN v_result || '{"idempotent_replay": true}'::JSONB; END IF;

    IF jsonb_typeof(p_items) <> 'array' OR jsonb_array_length(p_items) = 0 THEN
        RAISE EXCEPTION 'approved items are required' USING ERRCODE = '22023';
    END IF;

    IF NOT EXISTS (SELECT 1 FROM public.agent_runs WHERE id = p_run_id AND user_id = p_user_id) THEN
        RAISE EXCEPTION 'workflow run not found or not owned' USING ERRCODE = '42501';
    END IF;

    FOR v_item IN SELECT value FROM jsonb_array_elements(p_items)
    LOOP
        INSERT INTO public.commitments (
            id, user_id, title, description, type, status, deadline_at, start_before_at,
            estimated_minutes, actual_minutes, importance, flexibility, progress_percent,
            risk_score, risk_level, confidence_score
        ) VALUES (
            (v_item->>'id')::UUID, p_user_id, v_item->>'title', v_item->>'description',
            (v_item->>'type')::public.commitment_type, 'active',
            NULLIF(v_item->>'deadline_at', '')::TIMESTAMPTZ, NULLIF(v_item->>'start_before_at', '')::TIMESTAMPTZ,
            COALESCE((v_item->>'estimated_minutes')::INTEGER, 0), 0,
            (v_item->>'importance')::INTEGER, (v_item->>'flexibility')::INTEGER, 0,
            (v_item->>'risk_score')::DOUBLE PRECISION, (v_item->>'risk_level')::public.risk_level_type,
            (v_item->>'confidence_score')::DOUBLE PRECISION
        );

        FOR v_task IN SELECT value FROM jsonb_array_elements(COALESCE(v_item->'tasks', '[]'::JSONB))
        LOOP
            INSERT INTO public.tasks (
                id, commitment_id, user_id, title, next_action, done_condition,
                estimated_minutes, actual_minutes, status, sequence_order
            ) VALUES (
                (v_task->>'id')::UUID, (v_item->>'id')::UUID, p_user_id,
                v_task->>'title', v_task->>'next_action', v_task->>'done_condition',
                COALESCE((v_task->>'estimated_minutes')::INTEGER, 0), 0, 'pending',
                (v_task->>'sequence_order')::INTEGER
            );
        END LOOP;

        INSERT INTO public.time_spines (id, commitment_id, user_id, spine_json, current_stage)
        VALUES (
            (v_item->'time_spine'->>'id')::UUID,
            (v_item->>'id')::UUID,
            p_user_id,
            v_item->'time_spine'->'stages',
            v_item->'time_spine'->>'current_stage'
        );
        v_ids := v_ids || jsonb_build_array(v_item->>'id');
    END LOOP;

    INSERT INTO public.agent_trace_events (agent_run_id, user_id, step_name, status, explanation, payload_json)
    VALUES (p_run_id, p_user_id, 'approval_completed', 'succeeded', 'Approved commitment persistence completed atomically.', jsonb_build_object('count', jsonb_array_length(p_items)));
    UPDATE public.agent_runs SET status = 'completed', output_json = jsonb_build_object('approved_count', jsonb_array_length(p_items)), completed_at = now()
      WHERE id = p_run_id AND user_id = p_user_id;

    v_result := jsonb_build_object('status', 'success', 'count', jsonb_array_length(p_items), 'commitment_ids', v_ids, 'idempotent_replay', false);
    INSERT INTO public.operation_receipts (user_id, operation_type, idempotency_key, result_json)
    VALUES (p_user_id, 'intake_approval', p_idempotency_key, v_result);
    RETURN v_result;
EXCEPTION WHEN OTHERS THEN
    IF SQLSTATE = '42501' THEN RAISE; END IF;
    IF EXISTS (SELECT 1 FROM public.agent_runs WHERE id = p_run_id AND user_id = p_user_id) THEN
        UPDATE public.agent_runs SET status = 'failed', error_message = 'persistence_failure', completed_at = now()
          WHERE id = p_run_id AND user_id = p_user_id;
        INSERT INTO public.agent_trace_events (agent_run_id, user_id, step_name, status, explanation, payload_json)
        VALUES (p_run_id, p_user_id, 'approval_failed', 'failed', 'Approved persistence rolled back without partial writes.', jsonb_build_object('error_code', 'persistence_failure'));
    END IF;
    RETURN jsonb_build_object('status', 'failed', 'error_code', 'persistence_failure');
END;
$$;

CREATE OR REPLACE FUNCTION public.complete_focus_transaction(
    p_user_id UUID,
    p_focus_block_id UUID,
    p_reflection_id UUID,
    p_idempotency_key TEXT,
    p_actual_minutes INTEGER,
    p_completion_status TEXT,
    p_energy_level INTEGER,
    p_progress_percent INTEGER,
    p_risk_score DOUBLE PRECISION,
    p_risk_level public.risk_level_type,
    p_blocker_reason TEXT DEFAULT NULL,
    p_notes TEXT DEFAULT NULL
) RETURNS JSONB
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, public
AS $$
DECLARE
    v_block public.focus_blocks%ROWTYPE;
    v_reflection public.reflections%ROWTYPE;
    v_result JSONB;
    v_planned INTEGER;
BEGIN
    IF COALESCE(auth.role(), '') <> 'service_role' AND auth.uid() IS DISTINCT FROM p_user_id THEN
        RAISE EXCEPTION 'ownership validation failed' USING ERRCODE = '42501';
    END IF;
    PERFORM pg_advisory_xact_lock(hashtextextended(p_user_id::TEXT || ':focus:' || p_idempotency_key, 0));
    SELECT result_json INTO v_result FROM public.operation_receipts
      WHERE user_id = p_user_id AND operation_type = 'focus_completion' AND idempotency_key = p_idempotency_key;
    IF v_result IS NOT NULL THEN RETURN v_result || '{"idempotent_replay": true}'::JSONB; END IF;

    SELECT * INTO v_block FROM public.focus_blocks WHERE id = p_focus_block_id AND user_id = p_user_id FOR UPDATE;
    IF NOT FOUND OR v_block.commitment_id IS NULL THEN
        RAISE EXCEPTION 'focus session not found or not owned' USING ERRCODE = '42501';
    END IF;
    IF NOT EXISTS (SELECT 1 FROM public.commitments WHERE id = v_block.commitment_id AND user_id = p_user_id) THEN
        RAISE EXCEPTION 'commitment not found or not owned' USING ERRCODE = '42501';
    END IF;
    v_planned := GREATEST(0, floor(extract(epoch FROM (v_block.end_at - v_block.start_at)) / 60)::INTEGER);

    UPDATE public.focus_blocks SET status = 'completed', paused_at = NULL WHERE id = p_focus_block_id AND user_id = p_user_id;
    INSERT INTO public.reflections (
        id, user_id, commitment_id, focus_block_id, planned_minutes, actual_minutes,
        completion_status, energy_level, blocker_reason, notes
    ) VALUES (
        p_reflection_id, p_user_id, v_block.commitment_id, p_focus_block_id, v_planned,
        p_actual_minutes, p_completion_status, p_energy_level, p_blocker_reason, p_notes
    ) RETURNING * INTO v_reflection;
    UPDATE public.commitments
       SET actual_minutes = actual_minutes + p_actual_minutes,
           progress_percent = p_progress_percent,
           risk_score = p_risk_score,
           risk_level = p_risk_level
     WHERE id = v_block.commitment_id AND user_id = p_user_id;
    UPDATE public.time_spines
       SET spine_json = (
            SELECT jsonb_agg(CASE WHEN entry->>'id' = 'next_action' THEN jsonb_set(entry, '{status}', '"completed"'::JSONB) ELSE entry END)
            FROM jsonb_array_elements(spine_json) entry
       ), current_stage = 'reflection'
     WHERE commitment_id = v_block.commitment_id AND user_id = p_user_id;

    v_result := jsonb_build_object('status', 'completed', 'focus_block_id', p_focus_block_id, 'commitment_id', v_block.commitment_id, 'reflection', to_jsonb(v_reflection), 'idempotent_replay', false);
    INSERT INTO public.operation_receipts (user_id, operation_type, idempotency_key, result_json)
    VALUES (p_user_id, 'focus_completion', p_idempotency_key, v_result);
    RETURN v_result;
EXCEPTION WHEN OTHERS THEN
    IF SQLSTATE = '42501' THEN RAISE; END IF;
    RETURN jsonb_build_object('status', 'failed', 'error_code', 'focus_completion_rolled_back');
END;
$$;

CREATE OR REPLACE FUNCTION public.approve_recovery_transaction(
    p_user_id UUID,
    p_proposal_id UUID,
    p_idempotency_key TEXT,
    p_focus_block_id UUID DEFAULT NULL
) RETURNS JSONB
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, public
AS $$
DECLARE
    v_proposal public.agent_proposed_actions%ROWTYPE;
    v_payload JSONB;
    v_result JSONB;
    v_created JSONB := NULL;
    v_start TIMESTAMPTZ;
    v_end TIMESTAMPTZ;
    v_block public.focus_blocks%ROWTYPE;
BEGIN
    IF COALESCE(auth.role(), '') <> 'service_role' AND auth.uid() IS DISTINCT FROM p_user_id THEN
        RAISE EXCEPTION 'ownership validation failed' USING ERRCODE = '42501';
    END IF;
    PERFORM pg_advisory_xact_lock(hashtextextended(p_user_id::TEXT || ':recovery:' || p_idempotency_key, 0));
    SELECT result_json INTO v_result FROM public.operation_receipts
      WHERE user_id = p_user_id AND operation_type = 'recovery_approval' AND idempotency_key = p_idempotency_key;
    IF v_result IS NOT NULL THEN RETURN v_result || '{"idempotent_replay": true}'::JSONB; END IF;

    SELECT * INTO v_proposal FROM public.agent_proposed_actions
      WHERE id = p_proposal_id AND user_id = p_user_id AND action_type = 'commitment_rescue' FOR UPDATE;
    IF NOT FOUND THEN RAISE EXCEPTION 'recovery proposal not found or not owned' USING ERRCODE = '42501'; END IF;
    IF v_proposal.status <> 'pending' THEN RAISE EXCEPTION 'recovery proposal is not pending' USING ERRCODE = '23514'; END IF;
    v_payload := v_proposal.payload_json;

    IF v_payload->>'rescue_action_type' = 'create_rescue_focus_block' THEN
        IF p_focus_block_id IS NULL THEN RAISE EXCEPTION 'focus block id is required' USING ERRCODE = '22023'; END IF;
        IF NOT EXISTS (SELECT 1 FROM public.commitments WHERE id = (v_payload->>'commitment_id')::UUID AND user_id = p_user_id) THEN
            RAISE EXCEPTION 'commitment not found or not owned' USING ERRCODE = '42501';
        END IF;
        v_start := (v_payload->>'start_at')::TIMESTAMPTZ;
        v_end := (v_payload->>'end_at')::TIMESTAMPTZ;
        IF v_end <= v_start THEN RAISE EXCEPTION 'invalid recovery block interval' USING ERRCODE = '22023'; END IF;
        IF EXISTS (SELECT 1 FROM public.focus_blocks WHERE user_id = p_user_id AND status NOT IN ('skipped', 'moved') AND start_at < v_end AND end_at > v_start)
           OR EXISTS (SELECT 1 FROM public.calendar_events WHERE user_id = p_user_id AND start_at < v_end AND end_at > v_start) THEN
            RAISE EXCEPTION 'recovery block overlaps existing time' USING ERRCODE = '23P01';
        END IF;
        INSERT INTO public.focus_blocks (id, user_id, commitment_id, title, start_at, end_at, block_type, status)
        VALUES (p_focus_block_id, p_user_id, (v_payload->>'commitment_id')::UUID, COALESCE(v_payload->>'title', 'Recovery focus'), v_start, v_end, 'deep_work', 'scheduled')
        RETURNING * INTO v_block;
        v_created := to_jsonb(v_block);
    END IF;

    UPDATE public.agent_proposed_actions SET status = 'approved' WHERE id = p_proposal_id AND user_id = p_user_id;
    INSERT INTO public.agent_trace_events (agent_run_id, user_id, step_name, status, explanation, payload_json)
    VALUES (v_proposal.agent_run_id, p_user_id, 'recovery_approved', 'succeeded', 'Approved recovery mutation applied atomically.', jsonb_build_object('proposal_id', p_proposal_id));
    v_result := jsonb_build_object('status', 'approved', 'action', v_payload->>'rescue_action_type', 'focus_block', v_created, 'idempotent_replay', false);
    INSERT INTO public.operation_receipts (user_id, operation_type, idempotency_key, result_json)
    VALUES (p_user_id, 'recovery_approval', p_idempotency_key, v_result);
    RETURN v_result;
EXCEPTION WHEN OTHERS THEN
    IF SQLSTATE = '42501' THEN RAISE; END IF;
    IF v_proposal.agent_run_id IS NOT NULL THEN
        INSERT INTO public.agent_trace_events (agent_run_id, user_id, step_name, status, explanation, payload_json)
        VALUES (v_proposal.agent_run_id, p_user_id, 'recovery_approval_failed', 'failed', 'Recovery approval rolled back without partial writes.', jsonb_build_object('error_code', 'recovery_approval_rolled_back'));
    END IF;
    RETURN jsonb_build_object('status', 'failed', 'error_code', 'recovery_approval_rolled_back');
END;
$$;

REVOKE ALL ON FUNCTION public.approve_intake_transaction(UUID, UUID, TEXT, JSONB) FROM PUBLIC, anon;
REVOKE ALL ON FUNCTION public.complete_focus_transaction(UUID, UUID, UUID, TEXT, INTEGER, TEXT, INTEGER, INTEGER, DOUBLE PRECISION, public.risk_level_type, TEXT, TEXT) FROM PUBLIC, anon;
REVOKE ALL ON FUNCTION public.approve_recovery_transaction(UUID, UUID, TEXT, UUID) FROM PUBLIC, anon;
GRANT EXECUTE ON FUNCTION public.approve_intake_transaction(UUID, UUID, TEXT, JSONB) TO authenticated, service_role;
GRANT EXECUTE ON FUNCTION public.complete_focus_transaction(UUID, UUID, UUID, TEXT, INTEGER, TEXT, INTEGER, INTEGER, DOUBLE PRECISION, public.risk_level_type, TEXT, TEXT) TO authenticated, service_role;
GRANT EXECUTE ON FUNCTION public.approve_recovery_transaction(UUID, UUID, TEXT, UUID) TO authenticated, service_role;
