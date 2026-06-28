-- Migration: 003_create_commitments.sql
-- Description: Core commitments table and indexes

-- 1. Create Enums if not exists
DO $$ BEGIN
    CREATE TYPE public.commitment_type AS ENUM (
        'hard_deadline', 
        'soft_deadline', 
        'event', 
        'habit', 
        'waiting_on', 
        'recurring_obligation', 
        'reference', 
        'someday'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE public.commitment_status AS ENUM (
        'inbox', 
        'clarified', 
        'planned', 
        'active', 
        'blocked', 
        'at_risk', 
        'rescue', 
        'completed', 
        'archived'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE public.risk_level_type AS ENUM (
        'stable', 
        'watch', 
        'at_risk', 
        'critical', 
        'rescue_required'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- 2. Create Commitments Table
CREATE TABLE public.commitments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES public.user_profiles(id) ON DELETE CASCADE NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    type public.commitment_type DEFAULT 'hard_deadline'::public.commitment_type NOT NULL,
    status public.commitment_status DEFAULT 'inbox'::public.commitment_status NOT NULL,
    deadline_at TIMESTAMP WITH TIME ZONE,
    start_before_at TIMESTAMP WITH TIME ZONE,
    estimated_minutes INTEGER DEFAULT 0 NOT NULL,
    actual_minutes INTEGER DEFAULT 0 NOT NULL,
    importance INTEGER DEFAULT 3 CHECK (importance BETWEEN 1 AND 5) NOT NULL,
    consequence TEXT,
    flexibility INTEGER DEFAULT 3 CHECK (flexibility BETWEEN 1 AND 5) NOT NULL,
    progress_percent INTEGER DEFAULT 0 CHECK (progress_percent BETWEEN 0 AND 100) NOT NULL,
    risk_level public.risk_level_type DEFAULT 'stable'::public.risk_level_type NOT NULL,
    risk_score FLOAT DEFAULT 0.0 NOT NULL,
    confidence_score FLOAT DEFAULT 1.0 NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL
);

-- 3. Create Indexes
CREATE INDEX idx_commitments_user_status ON public.commitments(user_id, status);
CREATE INDEX idx_commitments_deadline ON public.commitments(deadline_at);

-- 4. Hook updated_at trigger
CREATE TRIGGER update_commitments_modtime
    BEFORE UPDATE ON public.commitments
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

-- 5. Enable RLS
ALTER TABLE public.commitments ENABLE ROW LEVEL SECURITY;

-- 6. Explicit RLS Policies
CREATE POLICY "Users can select their own commitments"
    ON public.commitments FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own commitments"
    ON public.commitments FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own commitments"
    ON public.commitments FOR UPDATE
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can delete their own commitments"
    ON public.commitments FOR DELETE
    USING (auth.uid() = user_id);
