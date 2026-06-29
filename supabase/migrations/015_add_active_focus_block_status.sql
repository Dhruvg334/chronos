-- Migration: 015_add_active_focus_block_status.sql
-- Description: Add active status for running focus blocks.

ALTER TYPE public.block_status_enum ADD VALUE IF NOT EXISTS 'active';
