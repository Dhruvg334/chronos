-- Migration: 023_harden_adaptive_plan_approval_rpc.sql
-- Description: Remove the writable public schema from the adaptive-plan SECURITY DEFINER search path.

CREATE OR REPLACE FUNCTION public.approve_adaptive_plan_transaction(
    p_user_id UUID,
    p_proposal_id UUID,
    p_idempotency_key TEXT,
    p_block_ids UUID[]
) RETURNS JSONB
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog
AS $$
DECLARE
    v_proposal public.agent_proposed_actions%ROWTYPE;
    v_block JSONB;
    v_index INTEGER := 1;
    v_start TIMESTAMPTZ;
    v_end TIMESTAMPTZ;
    v_commitment UUID;
    v_created JSONB := '[]'::JSONB;
    v_result JSONB;
BEGIN
    IF COALESCE(auth.role(), '') <> 'service_role' AND auth.uid() IS DISTINCT FROM p_user_id THEN
        RAISE EXCEPTION 'ownership validation failed' USING ERRCODE = '42501';
    END IF;
    IF p_idempotency_key IS NULL OR length(p_idempotency_key) < 8 THEN
        RAISE EXCEPTION 'invalid idempotency key' USING ERRCODE = '22023';
    END IF;
    PERFORM pg_advisory_xact_lock(hashtextextended(p_user_id::TEXT || ':adaptive-plan:' || p_idempotency_key, 0));
    SELECT result_json INTO v_result FROM public.operation_receipts
      WHERE user_id = p_user_id AND operation_type = 'adaptive_plan_approval' AND idempotency_key = p_idempotency_key;
    IF v_result IS NOT NULL THEN RETURN v_result || '{"idempotent_replay": true}'::JSONB; END IF;

    SELECT * INTO v_proposal FROM public.agent_proposed_actions
      WHERE id = p_proposal_id AND user_id = p_user_id AND action_type = 'commitment_reschedule' FOR UPDATE;
    IF NOT FOUND THEN RAISE EXCEPTION 'adaptive plan proposal not found or not owned' USING ERRCODE = '42501'; END IF;
    IF v_proposal.status <> 'pending' THEN RAISE EXCEPTION 'adaptive plan proposal is not pending' USING ERRCODE = '23514'; END IF;
    IF jsonb_typeof(v_proposal.payload_json->'adaptive_plan'->'blocks') <> 'array'
       OR jsonb_array_length(v_proposal.payload_json->'adaptive_plan'->'blocks') = 0
       OR cardinality(p_block_ids) <> jsonb_array_length(v_proposal.payload_json->'adaptive_plan'->'blocks') THEN
        RAISE EXCEPTION 'adaptive plan block identifiers are invalid' USING ERRCODE = '22023';
    END IF;

    FOR v_block IN SELECT value FROM jsonb_array_elements(v_proposal.payload_json->'adaptive_plan'->'blocks')
    LOOP
        v_commitment := (v_block->>'commitment_id')::UUID;
        v_start := (v_block->>'start_at')::TIMESTAMPTZ;
        v_end := v_start + make_interval(mins => (v_block->>'duration_minutes')::INTEGER);
        IF v_end <= v_start THEN RAISE EXCEPTION 'invalid adaptive plan interval' USING ERRCODE = '22023'; END IF;
        IF NOT EXISTS (
            SELECT 1 FROM public.commitments
             WHERE id = v_commitment AND user_id = p_user_id AND status <> 'blocked' AND type <> 'waiting_on'
        ) THEN
            RAISE EXCEPTION 'commitment is unavailable or not owned' USING ERRCODE = '42501';
        END IF;
        IF EXISTS (
            SELECT 1 FROM public.focus_blocks
             WHERE user_id = p_user_id AND status NOT IN ('skipped', 'moved') AND start_at < v_end AND end_at > v_start
        ) OR EXISTS (
            SELECT 1 FROM public.calendar_events
             WHERE user_id = p_user_id AND start_at < v_end AND end_at > v_start
        ) THEN
            RAISE EXCEPTION 'adaptive plan overlaps existing time' USING ERRCODE = '23P01';
        END IF;
        INSERT INTO public.focus_blocks (id, user_id, commitment_id, title, start_at, end_at, block_type, status)
        SELECT p_block_ids[v_index], p_user_id, v_commitment, c.title, v_start, v_end, 'deep_work', 'scheduled'
          FROM public.commitments c WHERE c.id = v_commitment AND c.user_id = p_user_id;
        v_created := v_created || jsonb_build_array(p_block_ids[v_index]);
        v_index := v_index + 1;
    END LOOP;

    UPDATE public.agent_proposed_actions SET status = 'approved' WHERE id = p_proposal_id AND user_id = p_user_id;
    INSERT INTO public.agent_trace_events (agent_run_id, user_id, step_name, status, explanation, payload_json)
    VALUES (v_proposal.agent_run_id, p_user_id, 'adaptive_plan_approved', 'succeeded', 'Approved adaptive plan applied atomically.', jsonb_build_object('block_count', jsonb_array_length(v_created)));
    v_result := jsonb_build_object('status', 'approved', 'block_ids', v_created, 'idempotent_replay', false);
    INSERT INTO public.operation_receipts (user_id, operation_type, idempotency_key, result_json)
    VALUES (p_user_id, 'adaptive_plan_approval', p_idempotency_key, v_result);
    RETURN v_result;
EXCEPTION WHEN OTHERS THEN
    IF SQLSTATE = '42501' THEN RAISE; END IF;
    RETURN jsonb_build_object('status', 'failed', 'error_code', 'adaptive_plan_approval_rolled_back');
END;
$$;

REVOKE ALL ON FUNCTION public.approve_adaptive_plan_transaction(UUID, UUID, TEXT, UUID[]) FROM PUBLIC, anon;
GRANT EXECUTE ON FUNCTION public.approve_adaptive_plan_transaction(UUID, UUID, TEXT, UUID[]) TO authenticated, service_role;
