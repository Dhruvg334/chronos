-- Migration: 010_create_agent_trace_events.sql
-- Description: Detailed steps executed within agent runs

CREATE TABLE public.agent_trace_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_run_id UUID REFERENCES public.agent_runs(id) ON DELETE CASCADE NOT NULL,
    user_id UUID REFERENCES public.user_profiles(id) ON DELETE CASCADE NOT NULL,
    step_name TEXT NOT NULL,
    tool_name TEXT,
    status TEXT NOT NULL, -- started, succeeded, failed
    explanation TEXT NOT NULL,
    payload_json JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL
);

-- Indexes
CREATE INDEX idx_trace_events_run ON public.agent_trace_events(agent_run_id);

-- Enable RLS
ALTER TABLE public.agent_trace_events ENABLE ROW LEVEL SECURITY;

-- Explicit RLS Policies
CREATE POLICY "Users can select their own trace events"
    ON public.agent_trace_events FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own trace events"
    ON public.agent_trace_events FOR INSERT
    WITH CHECK (auth.uid() = user_id);
