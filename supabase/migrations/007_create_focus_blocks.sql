-- Migration: 007_create_focus_blocks.sql
-- Description: Dedicated calendar focus blocks

-- 1. Create Enums if not exists
DO $$ BEGIN
    CREATE TYPE public.block_type_enum AS ENUM (
        'deep_work', 
        'shallow_work', 
        'admin', 
        'buffer', 
        'rescue_block', 
        'feedback_gate', 
        'reflection'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE public.block_status_enum AS ENUM (
        'scheduled', 
        'completed', 
        'skipped', 
        'moved'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- 2. Create Focus Blocks Table
CREATE TABLE public.focus_blocks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES public.user_profiles(id) ON DELETE CASCADE NOT NULL,
    commitment_id UUID REFERENCES public.commitments(id) ON DELETE SET NULL,
    title TEXT NOT NULL,
    start_at TIMESTAMP WITH TIME ZONE NOT NULL,
    end_at TIMESTAMP WITH TIME ZONE NOT NULL,
    block_type public.block_type_enum DEFAULT 'deep_work'::public.block_type_enum NOT NULL,
    status public.block_status_enum DEFAULT 'scheduled'::public.block_status_enum NOT NULL,
    google_event_id TEXT, -- Synced GCal event ID if applicable
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL
);

-- 3. Indexes
CREATE INDEX idx_focus_blocks_user_time ON public.focus_blocks(user_id, start_at, end_at);

-- 4. Hook updated_at trigger
CREATE TRIGGER update_focus_blocks_modtime
    BEFORE UPDATE ON public.focus_blocks
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

-- 5. Enable RLS
ALTER TABLE public.focus_blocks ENABLE ROW LEVEL SECURITY;

-- 6. Explicit RLS Policies
CREATE POLICY "Users can select their own focus blocks"
    ON public.focus_blocks FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own focus blocks"
    ON public.focus_blocks FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own focus blocks"
    ON public.focus_blocks FOR UPDATE
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can delete their own focus blocks"
    ON public.focus_blocks FOR DELETE
    USING (auth.uid() = user_id);
