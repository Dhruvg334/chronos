-- Migration: 002_create_google_connections.sql
-- Description: Decoupled table for storing Google connections and tokens

CREATE TABLE public.google_connections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES public.user_profiles(id) ON DELETE CASCADE UNIQUE NOT NULL,
    google_email TEXT NOT NULL,
    access_token TEXT NOT NULL,
    refresh_token TEXT NOT NULL,
    token_uri TEXT NOT NULL,
    client_id TEXT NOT NULL,
    scopes TEXT[] NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL
);

-- Hook updated_at trigger
CREATE TRIGGER update_google_connections_modtime
    BEFORE UPDATE ON public.google_connections
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

-- Enable RLS
ALTER TABLE public.google_connections ENABLE ROW LEVEL SECURITY;

-- Explicit RLS Policies
CREATE POLICY "Users can select their own Google connection"
    ON public.google_connections FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own Google connection"
    ON public.google_connections FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own Google connection"
    ON public.google_connections FOR UPDATE
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can delete their own Google connection"
    ON public.google_connections FOR DELETE
    USING (auth.uid() = user_id);
