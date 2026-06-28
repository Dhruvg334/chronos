-- Migration: 005_create_time_spines.sql
-- Description: Time Spines configuration storage

CREATE TABLE public.time_spines (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    commitment_id UUID REFERENCES public.commitments(id) ON DELETE CASCADE UNIQUE NOT NULL,
    user_id UUID REFERENCES public.user_profiles(id) ON DELETE CASCADE NOT NULL,
    spine_json JSONB NOT NULL,
    current_stage TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL
);

-- Hook updated_at trigger
CREATE TRIGGER update_time_spines_modtime
    BEFORE UPDATE ON public.time_spines
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

-- Enable RLS
ALTER TABLE public.time_spines ENABLE ROW LEVEL SECURITY;

-- Explicit RLS Policies
CREATE POLICY "Users can select their own time spines"
    ON public.time_spines FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own time spines"
    ON public.time_spines FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own time spines"
    ON public.time_spines FOR UPDATE
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can delete their own time spines"
    ON public.time_spines FOR DELETE
    USING (auth.uid() = user_id);
