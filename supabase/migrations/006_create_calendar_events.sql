-- Migration: 006_create_calendar_events.sql
-- Description: Calendar events cache with compound tenant unique index

CREATE TABLE public.calendar_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES public.user_profiles(id) ON DELETE CASCADE NOT NULL,
    google_event_id TEXT, -- Nullable for manual local events
    title TEXT NOT NULL,
    start_at TIMESTAMP WITH TIME ZONE NOT NULL,
    end_at TIMESTAMP WITH TIME ZONE NOT NULL,
    source TEXT DEFAULT 'google' NOT NULL,
    is_chronos_created BOOLEAN DEFAULT FALSE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL,
    -- Compound Unique constraint to isolate external events safely per user
    CONSTRAINT unique_user_google_event UNIQUE (user_id, google_event_id)
);

-- Indexes
CREATE INDEX idx_calendar_events_user_time ON public.calendar_events(user_id, start_at, end_at);

-- Hook updated_at trigger
CREATE TRIGGER update_calendar_events_modtime
    BEFORE UPDATE ON public.calendar_events
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

-- Enable RLS
ALTER TABLE public.calendar_events ENABLE ROW LEVEL SECURITY;

-- Explicit RLS Policies
CREATE POLICY "Users can select their own calendar events"
    ON public.calendar_events FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own calendar events"
    ON public.calendar_events FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own calendar events"
    ON public.calendar_events FOR UPDATE
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can delete their own calendar events"
    ON public.calendar_events FOR DELETE
    USING (auth.uid() = user_id);
