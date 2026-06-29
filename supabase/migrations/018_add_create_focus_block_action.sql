-- Migration: 018_add_create_focus_block_action.sql
-- Description: Add 'create_focus_block' to proposed_action_type enum

DO $$ BEGIN
    ALTER TYPE public.proposed_action_type ADD VALUE IF NOT EXISTS 'create_focus_block';
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;
