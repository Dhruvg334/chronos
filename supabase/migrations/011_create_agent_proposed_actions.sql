-- Migration: 011_create_agent_proposed_actions.sql
-- Description: Actions proposed by agents requiring human approval

-- 1. Create Enums if not exists
DO $$ BEGIN
    CREATE TYPE public.proposed_action_type AS ENUM (
        'calendar_create', 
        'calendar_move', 
        'calendar_delete', 
        'commitment_reschedule', 
        'commitment_rescue', 
        'negotiation_send'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE public.proposed_action_status AS ENUM (
        'pending', 
        'approved', 
        'rejected', 
        'expired'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- 2. Create Agent Proposed Actions Table
CREATE TABLE public.agent_proposed_actions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES public.user_profiles(id) ON DELETE CASCADE NOT NULL,
    agent_run_id UUID REFERENCES public.agent_runs(id) ON DELETE CASCADE NOT NULL,
    action_type public.proposed_action_type NOT NULL,
    status public.proposed_action_status DEFAULT 'pending'::public.proposed_action_status NOT NULL,
    payload_json JSONB NOT NULL,
    explanation TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL
);

-- Hook updated_at trigger
CREATE TRIGGER update_agent_proposed_actions_modtime
    BEFORE UPDATE ON public.agent_proposed_actions
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

-- Enable RLS
ALTER TABLE public.agent_proposed_actions ENABLE ROW LEVEL SECURITY;

-- Explicit RLS Policies
CREATE POLICY "Users can select their own proposed actions"
    ON public.agent_proposed_actions FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own proposed actions"
    ON public.agent_proposed_actions FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own proposed actions"
    ON public.agent_proposed_actions FOR UPDATE
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can delete their own proposed actions"
    ON public.agent_proposed_actions FOR DELETE
    USING (auth.uid() = user_id);
