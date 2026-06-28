-- Migration: 013_create_user_memory.sql
-- Description: Core user memory key-value mappings

CREATE TABLE public.user_memory (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES public.user_profiles(id) ON DELETE CASCADE NOT NULL,
    memory_type TEXT NOT NULL, -- overrun_factor, preferred_hours, energy_mapping, etc.
    key TEXT NOT NULL,
    value_json JSONB NOT NULL,
    confidence FLOAT DEFAULT 0.5 NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL,
    UNIQUE (user_id, memory_type, key)
);

-- Hook updated_at trigger
CREATE TRIGGER update_user_memory_modtime
    BEFORE UPDATE ON public.user_memory
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

-- Enable RLS
ALTER TABLE public.user_memory ENABLE ROW LEVEL SECURITY;

-- Explicit RLS Policies
CREATE POLICY "Users can select their own memory logs"
    ON public.user_memory FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own memory logs"
    ON public.user_memory FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own memory logs"
    ON public.user_memory FOR UPDATE
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can delete their own memory logs"
    ON public.user_memory FOR DELETE
    USING (auth.uid() = user_id);
