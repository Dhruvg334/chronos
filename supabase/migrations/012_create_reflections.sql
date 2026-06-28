-- Migration: 012_create_reflections.sql
-- Description: Reflections logged after completing focus blocks or commitments

CREATE TABLE public.reflections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES public.user_profiles(id) ON DELETE CASCADE NOT NULL,
    commitment_id UUID REFERENCES public.commitments(id) ON DELETE SET NULL,
    focus_block_id UUID REFERENCES public.focus_blocks(id) ON DELETE SET NULL,
    planned_minutes INTEGER NOT NULL,
    actual_minutes INTEGER NOT NULL,
    completion_status TEXT NOT NULL, -- completed, partial, skipped
    energy_level INTEGER CHECK (energy_level BETWEEN 1 AND 5) NOT NULL,
    blocker_reason TEXT,
    quality_confidence TEXT,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL
);

-- Enable RLS
ALTER TABLE public.reflections ENABLE ROW LEVEL SECURITY;

-- Explicit RLS Policies
CREATE POLICY "Users can select their own reflections"
    ON public.reflections FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own reflections"
    ON public.reflections FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own reflections"
    ON public.reflections FOR UPDATE
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can delete their own reflections"
    ON public.reflections FOR DELETE
    USING (auth.uid() = user_id);
