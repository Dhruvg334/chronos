-- Migration: 009_create_agent_runs.sql
-- Description: Agent run logs and parameters

CREATE TABLE public.agent_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES public.user_profiles(id) ON DELETE CASCADE NOT NULL,
    run_type TEXT NOT NULL, -- intake, replan, rescue, etc.
    status TEXT NOT NULL, -- running, completed, failed
    input_json JSONB NOT NULL,
    output_json JSONB,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL,
    completed_at TIMESTAMP WITH TIME ZONE
);

-- Enable RLS
ALTER TABLE public.agent_runs ENABLE ROW LEVEL SECURITY;

-- Explicit RLS Policies
CREATE POLICY "Users can select their own agent runs"
    ON public.agent_runs FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own agent runs"
    ON public.agent_runs FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own agent runs"
    ON public.agent_runs FOR UPDATE
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);
