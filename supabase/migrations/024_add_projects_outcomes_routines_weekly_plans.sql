-- Additive personal-planning domains and atomic weekly-plan approval.

CREATE TABLE public.projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.user_profiles(id) ON DELETE CASCADE,
    title TEXT NOT NULL CHECK (length(title) BETWEEN 1 AND 180),
    description TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active','paused','completed','archived')),
    target_date DATE,
    colour TEXT NOT NULL DEFAULT 'accent' CHECK (length(colour) BETWEEN 1 AND 32),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (id, user_id)
);

CREATE TABLE public.outcomes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID,
    user_id UUID NOT NULL REFERENCES public.user_profiles(id) ON DELETE CASCADE,
    title TEXT NOT NULL CHECK (length(title) BETWEEN 1 AND 180),
    description TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active','blocked','uncertain','completed','archived')),
    target_date DATE,
    importance SMALLINT NOT NULL DEFAULT 3 CHECK (importance BETWEEN 1 AND 5),
    estimated_effort_minutes INTEGER CHECK (estimated_effort_minutes IS NULL OR estimated_effort_minutes BETWEEN 5 AND 100000),
    confidence DOUBLE PRECISION NOT NULL DEFAULT 0.5 CHECK (confidence BETWEEN 0 AND 1),
    completion_criteria TEXT NOT NULL CHECK (length(completion_criteria) BETWEEN 1 AND 1000),
    provenance TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (id, user_id),
    FOREIGN KEY (project_id, user_id) REFERENCES public.projects(id, user_id) ON DELETE SET NULL (project_id)
);

CREATE TABLE public.routines (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.user_profiles(id) ON DELETE CASCADE,
    title TEXT NOT NULL CHECK (length(title) BETWEEN 1 AND 180),
    frequency_rule TEXT NOT NULL DEFAULT 'weekly' CHECK (frequency_rule IN ('daily','weekly')),
    preferred_days SMALLINT[] NOT NULL CHECK (cardinality(preferred_days) BETWEEN 1 AND 7 AND preferred_days <@ ARRAY[0,1,2,3,4,5,6]::SMALLINT[]),
    preferred_time TIME,
    minimum_viable_version TEXT NOT NULL CHECK (length(minimum_viable_version) BETWEEN 1 AND 500),
    estimated_duration_minutes INTEGER NOT NULL CHECK (estimated_duration_minutes BETWEEN 5 AND 480),
    active BOOLEAN NOT NULL DEFAULT true,
    continuity_json JSONB NOT NULL DEFAULT '{"recent_completions":0,"last_status":null,"last_occurrence_date":null}'::JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (id, user_id)
);

CREATE TABLE public.routine_occurrences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    routine_id UUID NOT NULL,
    user_id UUID NOT NULL REFERENCES public.user_profiles(id) ON DELETE CASCADE,
    occurrence_date DATE NOT NULL,
    status TEXT NOT NULL DEFAULT 'due' CHECK (status IN ('due','completed','minimum_completed','skipped')),
    note TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (routine_id, occurrence_date),
    FOREIGN KEY (routine_id, user_id) REFERENCES public.routines(id, user_id) ON DELETE CASCADE
);

CREATE TABLE public.weekly_plans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.user_profiles(id) ON DELETE CASCADE,
    week_start DATE NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending','approved','rejected')),
    proposal_json JSONB NOT NULL DEFAULT '{}'::JSONB,
    explanation_json JSONB NOT NULL DEFAULT '{}'::JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (id, user_id)
);

ALTER TABLE public.commitments ADD COLUMN project_id UUID, ADD COLUMN outcome_id UUID;
ALTER TABLE public.commitments
    ADD CONSTRAINT commitments_project_owner_fk FOREIGN KEY (project_id, user_id) REFERENCES public.projects(id, user_id) ON DELETE SET NULL (project_id),
    ADD CONSTRAINT commitments_outcome_owner_fk FOREIGN KEY (outcome_id, user_id) REFERENCES public.outcomes(id, user_id) ON DELETE SET NULL (outcome_id);
ALTER TABLE public.tasks ADD COLUMN outcome_id UUID;
ALTER TABLE public.tasks ADD CONSTRAINT tasks_outcome_owner_fk FOREIGN KEY (outcome_id, user_id) REFERENCES public.outcomes(id, user_id) ON DELETE SET NULL (outcome_id);

CREATE INDEX idx_projects_user_status ON public.projects(user_id, status);
CREATE INDEX idx_outcomes_user_project_status ON public.outcomes(user_id, project_id, status);
CREATE INDEX idx_routines_user_active ON public.routines(user_id, active);
CREATE INDEX idx_routine_occurrences_user_date ON public.routine_occurrences(user_id, occurrence_date);
CREATE INDEX idx_weekly_plans_user_week ON public.weekly_plans(user_id, week_start);

CREATE TRIGGER update_projects_modtime BEFORE UPDATE ON public.projects FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();
CREATE TRIGGER update_outcomes_modtime BEFORE UPDATE ON public.outcomes FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();
CREATE TRIGGER update_routines_modtime BEFORE UPDATE ON public.routines FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();
CREATE TRIGGER update_routine_occurrences_modtime BEFORE UPDATE ON public.routine_occurrences FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();
CREATE TRIGGER update_weekly_plans_modtime BEFORE UPDATE ON public.weekly_plans FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

ALTER TABLE public.projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.outcomes ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.routines ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.routine_occurrences ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.weekly_plans ENABLE ROW LEVEL SECURITY;

CREATE POLICY projects_owner_all ON public.projects FOR ALL USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);
CREATE POLICY outcomes_owner_all ON public.outcomes FOR ALL USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);
CREATE POLICY routines_owner_all ON public.routines FOR ALL USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);
CREATE POLICY routine_occurrences_owner_all ON public.routine_occurrences FOR ALL USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);
CREATE POLICY weekly_plans_owner_all ON public.weekly_plans FOR ALL USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);

REVOKE ALL ON public.projects, public.outcomes, public.routines, public.routine_occurrences, public.weekly_plans FROM PUBLIC, anon;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.projects, public.outcomes, public.routines, public.routine_occurrences, public.weekly_plans TO authenticated;
GRANT ALL ON public.projects, public.outcomes, public.routines, public.routine_occurrences, public.weekly_plans TO service_role;

CREATE OR REPLACE FUNCTION public.approve_weekly_plan_transaction(
    p_user_id UUID, p_plan_id UUID, p_idempotency_key TEXT, p_block_ids UUID[]
) RETURNS JSONB
LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog
AS $$
DECLARE
    v_plan public.weekly_plans%ROWTYPE;
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
    PERFORM pg_advisory_xact_lock(hashtextextended(p_user_id::TEXT || ':weekly-plan:' || p_idempotency_key, 0));
    SELECT result_json INTO v_result FROM public.operation_receipts
      WHERE user_id = p_user_id AND operation_type = 'weekly_plan_approval' AND idempotency_key = p_idempotency_key;
    IF v_result IS NOT NULL THEN RETURN v_result || '{"idempotent_replay":true}'::JSONB; END IF;

    SELECT * INTO v_plan FROM public.weekly_plans WHERE id = p_plan_id AND user_id = p_user_id FOR UPDATE;
    IF NOT FOUND THEN RAISE EXCEPTION 'weekly plan not found or not owned' USING ERRCODE = '42501'; END IF;
    IF v_plan.status <> 'pending' THEN RAISE EXCEPTION 'weekly plan is no longer pending' USING ERRCODE = '23514'; END IF;
    IF jsonb_typeof(v_plan.proposal_json->'blocks') <> 'array'
       OR cardinality(p_block_ids) <> jsonb_array_length(v_plan.proposal_json->'blocks') THEN
        RAISE EXCEPTION 'weekly block identifiers are invalid' USING ERRCODE = '22023';
    END IF;

    FOR v_block IN SELECT value FROM jsonb_array_elements(v_plan.proposal_json->'blocks') LOOP
        v_commitment := (v_block->>'commitment_id')::UUID;
        v_start := (v_block->>'start_at')::TIMESTAMPTZ;
        v_end := v_start + make_interval(mins => (v_block->>'duration_minutes')::INTEGER);
        IF NOT EXISTS (SELECT 1 FROM public.commitments WHERE id = v_commitment AND user_id = p_user_id AND status <> 'blocked') THEN
            RAISE EXCEPTION 'commitment unavailable or not owned' USING ERRCODE = '42501';
        END IF;
        IF v_end <= v_start OR EXISTS (
            SELECT 1 FROM public.focus_blocks WHERE user_id = p_user_id AND status NOT IN ('skipped','moved') AND start_at < v_end AND end_at > v_start
        ) OR EXISTS (
            SELECT 1 FROM public.calendar_events WHERE user_id = p_user_id AND start_at < v_end AND end_at > v_start
        ) THEN RAISE EXCEPTION 'weekly block conflict' USING ERRCODE = '23P01'; END IF;
        INSERT INTO public.focus_blocks (id,user_id,commitment_id,title,start_at,end_at,block_type,status)
        SELECT p_block_ids[v_index],p_user_id,v_commitment,c.title,v_start,v_end,'deep_work','scheduled'
          FROM public.commitments c WHERE c.id=v_commitment AND c.user_id=p_user_id;
        v_created := v_created || jsonb_build_array(p_block_ids[v_index]);
        v_index := v_index + 1;
    END LOOP;
    UPDATE public.weekly_plans SET status='approved' WHERE id=p_plan_id AND user_id=p_user_id;
    v_result := jsonb_build_object('status','approved','block_ids',v_created,'idempotent_replay',false);
    INSERT INTO public.operation_receipts(user_id,operation_type,idempotency_key,result_json)
    VALUES(p_user_id,'weekly_plan_approval',p_idempotency_key,v_result);
    RETURN v_result;
EXCEPTION WHEN OTHERS THEN
    IF SQLSTATE='42501' THEN RAISE; END IF;
    RETURN jsonb_build_object('status','failed','error_code','weekly_plan_approval_rolled_back');
END;
$$;

REVOKE ALL ON FUNCTION public.approve_weekly_plan_transaction(UUID,UUID,TEXT,UUID[]) FROM PUBLIC, anon;
GRANT EXECUTE ON FUNCTION public.approve_weekly_plan_transaction(UUID,UUID,TEXT,UUID[]) TO authenticated, service_role;

CREATE OR REPLACE FUNCTION public.approve_planning_intake_transaction(
    p_user_id UUID, p_run_id UUID, p_idempotency_key TEXT, p_items JSONB
) RETURNS JSONB
LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog
AS $$
DECLARE
    v_item JSONB; v_task JSONB; v_kind TEXT; v_result JSONB; v_ids JSONB := '[]'::JSONB;
BEGIN
    IF COALESCE(auth.role(), '') <> 'service_role' AND auth.uid() IS DISTINCT FROM p_user_id THEN RAISE EXCEPTION 'ownership validation failed' USING ERRCODE='42501'; END IF;
    IF p_idempotency_key IS NULL OR length(p_idempotency_key)<8 OR jsonb_typeof(p_items)<>'array' OR jsonb_array_length(p_items)=0 THEN RAISE EXCEPTION 'invalid intake approval' USING ERRCODE='22023'; END IF;
    PERFORM pg_advisory_xact_lock(hashtextextended(p_user_id::TEXT || ':planning-intake:' || p_idempotency_key,0));
    SELECT result_json INTO v_result FROM public.operation_receipts WHERE user_id=p_user_id AND operation_type='intake_approval' AND idempotency_key=p_idempotency_key;
    IF v_result IS NOT NULL THEN RETURN v_result || '{"idempotent_replay":true}'::JSONB; END IF;
    IF NOT EXISTS(SELECT 1 FROM public.agent_runs WHERE id=p_run_id AND user_id=p_user_id) THEN RAISE EXCEPTION 'workflow run not owned' USING ERRCODE='42501'; END IF;
    FOR v_item IN SELECT value FROM jsonb_array_elements(p_items) LOOP
        v_kind := COALESCE(v_item->>'kind','task');
        IF NULLIF(v_item->>'project_id','') IS NOT NULL AND NOT EXISTS(SELECT 1 FROM public.projects WHERE id=(v_item->>'project_id')::UUID AND user_id=p_user_id) THEN RAISE EXCEPTION 'project not owned' USING ERRCODE='42501'; END IF;
        IF v_kind='routine' THEN
            INSERT INTO public.routines(id,user_id,title,frequency_rule,preferred_days,minimum_viable_version,estimated_duration_minutes,active)
            VALUES((v_item->>'id')::UUID,p_user_id,v_item->>'title','weekly',ARRAY(SELECT jsonb_array_elements_text(v_item->'preferred_days')::SMALLINT),v_item->>'minimum_viable_version',GREATEST(5,COALESCE((v_item->>'estimated_minutes')::INTEGER,5)),true);
        ELSIF v_kind='project_outcome' THEN
            INSERT INTO public.outcomes(id,project_id,user_id,title,description,status,target_date,importance,estimated_effort_minutes,confidence,completion_criteria,provenance)
            VALUES((v_item->>'id')::UUID,NULLIF(v_item->>'project_id','')::UUID,p_user_id,v_item->>'title',COALESCE(v_item->>'description',''),CASE WHEN (v_item->>'confidence_score')::DOUBLE PRECISION<0.6 THEN 'uncertain' ELSE 'active' END,NULLIF(left(v_item->>'deadline_at',10),'')::DATE,(v_item->>'importance')::SMALLINT,NULLIF(v_item->>'estimated_minutes','0')::INTEGER,(v_item->>'confidence_score')::DOUBLE PRECISION,v_item->>'completion_criteria','inbox');
        ELSE
            IF NULLIF(v_item->>'outcome_id','') IS NOT NULL AND NOT EXISTS(SELECT 1 FROM public.outcomes WHERE id=(v_item->>'outcome_id')::UUID AND user_id=p_user_id) THEN RAISE EXCEPTION 'outcome not owned' USING ERRCODE='42501'; END IF;
            INSERT INTO public.commitments(id,user_id,project_id,outcome_id,title,description,type,status,deadline_at,start_before_at,estimated_minutes,actual_minutes,importance,flexibility,progress_percent,risk_score,risk_level,confidence_score)
            VALUES((v_item->>'id')::UUID,p_user_id,NULLIF(v_item->>'project_id','')::UUID,NULLIF(v_item->>'outcome_id','')::UUID,v_item->>'title',v_item->>'description',(v_item->>'type')::public.commitment_type,'active',NULLIF(v_item->>'deadline_at','')::TIMESTAMPTZ,NULLIF(v_item->>'start_before_at','')::TIMESTAMPTZ,COALESCE((v_item->>'estimated_minutes')::INTEGER,0),0,(v_item->>'importance')::INTEGER,(v_item->>'flexibility')::INTEGER,0,(v_item->>'risk_score')::DOUBLE PRECISION,(v_item->>'risk_level')::public.risk_level_type,(v_item->>'confidence_score')::DOUBLE PRECISION);
            FOR v_task IN SELECT value FROM jsonb_array_elements(COALESCE(v_item->'tasks','[]'::JSONB)) LOOP
                INSERT INTO public.tasks(id,commitment_id,outcome_id,user_id,title,next_action,done_condition,estimated_minutes,actual_minutes,status,sequence_order)
                VALUES((v_task->>'id')::UUID,(v_item->>'id')::UUID,NULLIF(v_item->>'outcome_id','')::UUID,p_user_id,v_task->>'title',v_task->>'next_action',v_task->>'done_condition',COALESCE((v_task->>'estimated_minutes')::INTEGER,0),0,'pending',(v_task->>'sequence_order')::INTEGER);
            END LOOP;
            INSERT INTO public.time_spines(id,commitment_id,user_id,spine_json,current_stage) VALUES((v_item->'time_spine'->>'id')::UUID,(v_item->>'id')::UUID,p_user_id,v_item->'time_spine'->'stages',v_item->'time_spine'->>'current_stage');
        END IF;
        v_ids := v_ids || jsonb_build_array(v_item->>'id');
    END LOOP;
    INSERT INTO public.agent_trace_events(agent_run_id,user_id,step_name,status,explanation,payload_json) VALUES(p_run_id,p_user_id,'approval_completed','succeeded','Approved planning items persisted atomically.',jsonb_build_object('count',jsonb_array_length(p_items)));
    UPDATE public.agent_runs SET status='completed',output_json=jsonb_build_object('approved_count',jsonb_array_length(p_items)),completed_at=now() WHERE id=p_run_id AND user_id=p_user_id;
    v_result := jsonb_build_object('status','success','count',jsonb_array_length(p_items),'item_ids',v_ids,'idempotent_replay',false);
    INSERT INTO public.operation_receipts(user_id,operation_type,idempotency_key,result_json) VALUES(p_user_id,'intake_approval',p_idempotency_key,v_result);
    RETURN v_result;
EXCEPTION WHEN OTHERS THEN
    IF SQLSTATE='42501' THEN RAISE; END IF;
    RETURN jsonb_build_object('status','failed','error_code','planning_intake_rolled_back');
END;
$$;

REVOKE ALL ON FUNCTION public.approve_planning_intake_transaction(UUID,UUID,TEXT,JSONB) FROM PUBLIC, anon;
GRANT EXECUTE ON FUNCTION public.approve_planning_intake_transaction(UUID,UUID,TEXT,JSONB) TO authenticated, service_role;
