-- Migration: 016_add_last_synced_at_to_google_connections.sql
-- Description: Add last_synced_at column to google_connections

ALTER TABLE public.google_connections 
ADD COLUMN IF NOT EXISTS last_synced_at TIMESTAMP WITH TIME ZONE;
