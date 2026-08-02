-- Migration: 019_add_focus_session_lifecycle.sql
-- Description: Persist pause/resume timing and stop context for focus sessions.

ALTER TYPE public.block_status_enum ADD VALUE IF NOT EXISTS 'paused';

ALTER TABLE public.focus_blocks
    ADD COLUMN IF NOT EXISTS started_at TIMESTAMP WITH TIME ZONE,
    ADD COLUMN IF NOT EXISTS paused_at TIMESTAMP WITH TIME ZONE,
    ADD COLUMN IF NOT EXISTS accumulated_pause_seconds INTEGER DEFAULT 0 NOT NULL,
    ADD COLUMN IF NOT EXISTS stopped_reason TEXT;
