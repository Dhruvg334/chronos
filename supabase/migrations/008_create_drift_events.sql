-- Migration: 008_create_drift_events.sql
-- Description: Mismatches/deviations log table

CREATE TABLE public.drift_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES public.user_profiles(id) ON DELETE CASCADE NOT NULL,
    commitment_id UUID REFERENCES public.commitments(id) ON DELETE CASCADE NOT NULL,
    focus_block_id UUID REFERENCES public.focus_blocks(id) ON DELETE SET NULL,
    drift_type TEXT NOT NULL, -- task_overrun, task_underrun, skipped_block, etc.
    severity TEXT NOT NULL, -- info, warning, critical
    description TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL
);

-- Enable RLS
ALTER TABLE public.drift_events ENABLE ROW LEVEL SECURITY;

-- Explicit RLS Policies (Immutable logs - select/insert only, no update/delete by users)
CREATE POLICY "Users can select their own drift events"
    ON public.drift_events FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own drift events"
    ON public.drift_events FOR INSERT
    WITH CHECK (auth.uid() = user_id);
