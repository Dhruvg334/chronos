-- Seed file: supabase/seed.sql
-- Description: Seed data for ChronOS demo scenarios. Scoped to mock user 00000000-0000-0000-0000-000000000000.

-- 1. Create mock user profile
INSERT INTO public.user_profiles (id, display_name, timezone, working_hours_json, focus_preferences_json, autonomy_level)
VALUES (
    '00000000-0000-0000-0000-000000000000',
    'Demo User',
    'Asia/Kolkata',
    '{"start": "09:00", "end": "17:00", "days": [1,2,3,4,5]}'::jsonb,
    '{"deep_work_duration": 90, "shallow_work_duration": 30, "default_buffer_percent": 15}'::jsonb,
    'ask'::public.autonomy_level_type
) ON CONFLICT (id) DO NOTHING;

SELECT public.set_google_tokens(
    '00000000-0000-0000-0000-000000000000'::uuid,
    'demo@gmail.com',
    'mock_access_token',
    'mock_refresh_token',
    'https://oauth2.googleapis.com/token',
    'mock_client_id.apps.googleusercontent.com',
    ARRAY['https://www.googleapis.com/auth/calendar.readonly'],
    NOW() + INTERVAL '1 hour'
);


-- ============================================================================
-- SCENARIO A: Hackathon Week (Core Loop)
-- ============================================================================

-- Commitments
INSERT INTO public.commitments (id, user_id, title, description, type, status, deadline_at, estimated_minutes, actual_minutes, importance, consequence, flexibility, progress_percent, risk_level, risk_score)
VALUES (
    'a0000000-0000-0000-0000-000000000000',
    '00000000-0000-0000-0000-000000000000',
    'Vibe2Ship Hackathon Demo',
    'Complete the ChronOS agent flow and frontend canvas.',
    'hard_deadline'::public.commitment_type,
    'active'::public.commitment_status,
    NOW() + INTERVAL '3 days',
    1200,
    0,
    5,
    'Lose hackathon submission deadline',
    2,
    10,
    'stable'::public.risk_level_type,
    25.0
) ON CONFLICT (id) DO NOTHING;

-- Tasks
INSERT INTO public.tasks (id, commitment_id, user_id, title, next_action, done_condition, estimated_minutes, status, sequence_order)
VALUES 
('a0000000-0000-0000-0000-000000000001', 'a0000000-0000-0000-0000-000000000000', '00000000-0000-0000-0000-000000000000', 'Build frontend landing page', 'Design CSS layout and buttons', 'Landing page builds without errors', 180, 'completed', 1),
('a0000000-0000-0000-0000-000000000002', 'a0000000-0000-0000-0000-000000000000', '00000000-0000-0000-0000-000000000000', 'Implement API tests', 'Write pytest modules for endpoint health', 'All unit tests pass successfully', 120, 'pending', 2),
('a0000000-0000-0000-0000-000000000003', 'a0000000-0000-0000-0000-000000000000', '00000000-0000-0000-0000-000000000000', 'Record demo video', 'Script transitions and record screen', 'Generate 3-minute mp4 upload', 90, 'pending', 3)
ON CONFLICT (id) DO NOTHING;

-- Focus blocks
INSERT INTO public.focus_blocks (id, user_id, commitment_id, title, start_at, end_at, block_type, status)
VALUES 
('a0000000-0000-0000-0000-000000000004', '00000000-0000-0000-0000-000000000000', 'a0000000-0000-0000-0000-000000000000', 'Frontend Coding', NOW() + INTERVAL '1 hour', NOW() + INTERVAL '4 hours', 'deep_work'::public.block_type_enum, 'scheduled'::public.block_status_enum),
('a0000000-0000-0000-0000-000000000005', '00000000-0000-0000-0000-000000000000', 'a0000000-0000-0000-0000-000000000000', 'API Testing', NOW() + INTERVAL '1 day', NOW() + INTERVAL '1 day 2 hours', 'shallow_work'::public.block_type_enum, 'scheduled'::public.block_status_enum)
ON CONFLICT (id) DO NOTHING;

-- Calendar events (Mocking academic constraints)
INSERT INTO public.calendar_events (id, user_id, google_event_id, title, start_at, end_at, source, is_chronos_created)
VALUES 
('a0000000-0000-0000-0000-000000000006', '00000000-0000-0000-0000-000000000000', 'g_class_1', 'Daily Classes (Constraint)', NOW() + INTERVAL '2 hours', NOW() + INTERVAL '6 hours', 'google', false)
ON CONFLICT (user_id, google_event_id) DO NOTHING;

-- Drift event
INSERT INTO public.drift_events (id, user_id, commitment_id, focus_block_id, drift_type, severity, description)
VALUES (
    'a0000000-0000-0000-0000-000000000007',
    '00000000-0000-0000-0000-000000000000',
    'a0000000-0000-0000-0000-000000000000',
    'a0000000-0000-0000-0000-000000000004',
    'task_overrun',
    'warning',
    'Frontend landing design and layout took 2 hours longer than planned.'
) ON CONFLICT (id) DO NOTHING;


-- ============================================================================
-- SCENARIO B: Assignment Crisis (Rescue Mode)
-- ============================================================================

-- Commitments
INSERT INTO public.commitments (id, user_id, title, description, type, status, deadline_at, estimated_minutes, actual_minutes, importance, consequence, flexibility, progress_percent, risk_level, risk_score)
VALUES (
    'b0000000-0000-0000-0000-000000000000',
    '00000000-0000-0000-0000-000000000000',
    'University Database Project',
    'Design PostgreSQL schemas, write triggers, and push to Git.',
    'hard_deadline'::public.commitment_type,
    'at_risk'::public.commitment_status,
    NOW() + INTERVAL '6 hours',
    300,
    0,
    4,
    'Fail the database course',
    1,
    0,
    'rescue_required'::public.risk_level_type,
    95.0
) ON CONFLICT (id) DO NOTHING;

-- Focus blocks (scheduled for database project)
INSERT INTO public.focus_blocks (id, user_id, commitment_id, title, start_at, end_at, block_type, status)
VALUES (
    'b0000000-0000-0000-0000-000000000001',
    '00000000-0000-0000-0000-000000000000',
    'b0000000-0000-0000-0000-000000000000',
    'Database Schema Setup',
    NOW() + INTERVAL '30 minutes',
    NOW() + INTERVAL '3 hours 30 minutes',
    'rescue_block'::public.block_type_enum,
    'scheduled'::public.block_status_enum
) ON CONFLICT (id) DO NOTHING;

-- Drift event
INSERT INTO public.drift_events (id, user_id, commitment_id, focus_block_id, drift_type, severity, description)
VALUES (
    'b0000000-0000-0000-0000-000000000002',
    '00000000-0000-0000-0000-000000000000',
    'b0000000-0000-0000-0000-000000000000',
    NULL,
    'skipped_block',
    'critical',
    'Procrastinated on schema definition; starting too late.'
) ON CONFLICT (id) DO NOTHING;


-- ============================================================================
-- SCENARIO C: Interview Prep Week (Long Horizon)
-- ============================================================================

-- Commitments
INSERT INTO public.commitments (id, user_id, title, description, type, status, deadline_at, estimated_minutes, actual_minutes, importance, consequence, flexibility, progress_percent, risk_level, risk_score)
VALUES (
    'c0000000-0000-0000-0000-000000000000',
    '00000000-0000-0000-0000-000000000000',
    'Technical Interview Prep',
    'Practice mock interviews and study algorithms.',
    'soft_deadline'::public.commitment_type,
    'active'::public.commitment_status,
    NOW() + INTERVAL '7 days',
    600,
    0,
    4,
    'Perform poorly on incoming company screens',
    4,
    20,
    'watch'::public.risk_level_type,
    45.0
) ON CONFLICT (id) DO NOTHING;

-- Focus blocks (Study & Feedback gate)
INSERT INTO public.focus_blocks (id, user_id, commitment_id, title, start_at, end_at, block_type, status)
VALUES 
('c0000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000000', 'c0000000-0000-0000-0000-000000000000', 'Algorithms Study', NOW() + INTERVAL '2 days', NOW() + INTERVAL '2 days 1.5 hours', 'deep_work'::public.block_type_enum, 'scheduled'::public.block_status_enum),
('c0000000-0000-0000-0000-000000000002', '00000000-0000-0000-0000-000000000000', 'c0000000-0000-0000-0000-000000000000', 'Resume Review Checkpoint', NOW() + INTERVAL '3 days', NOW() + INTERVAL '3 days 1 hour', 'feedback_gate'::public.block_type_enum, 'scheduled'::public.block_status_enum)
ON CONFLICT (id) DO NOTHING;

-- Drift event
INSERT INTO public.drift_events (id, user_id, commitment_id, focus_block_id, drift_type, severity, description)
VALUES (
    'c0000000-0000-0000-0000-000000000003',
    '00000000-0000-0000-0000-000000000000',
    'c0000000-0000-0000-0000-000000000000',
    NULL,
    'energy_drift',
    'info',
    'System Design mock review session rescheduled by partner.'
) ON CONFLICT (id) DO NOTHING;


-- ============================================================================
-- SCENARIO D: Busy Professional Day (Context-Aware Shielding)
-- ============================================================================

-- Commitments
INSERT INTO public.commitments (id, user_id, title, description, type, status, deadline_at, estimated_minutes, actual_minutes, importance, consequence, flexibility, progress_percent, risk_level, risk_score)
VALUES (
    'd0000000-0000-0000-0000-000000000000',
    '00000000-0000-0000-0000-000000000000',
    'Client Deliverable Release',
    'Perform code reviews and deploy build package to staging environment.',
    'hard_deadline'::public.commitment_type,
    'active'::public.commitment_status,
    NOW() + INTERVAL '12 hours',
    240,
    0,
    5,
    'Unsatisfied client SLA agreement',
    1,
    60,
    'at_risk'::public.risk_level_type,
    75.0
) ON CONFLICT (id) DO NOTHING;

-- Focus block
INSERT INTO public.focus_blocks (id, user_id, commitment_id, title, start_at, end_at, block_type, status)
VALUES (
    'd0000000-0000-0000-0000-000000000001',
    '00000000-0000-0000-0000-000000000000',
    'd0000000-0000-0000-0000-000000000000',
    'Final Code Review Block',
    NOW() + INTERVAL '4 hours',
    NOW() + INTERVAL '6 hours',
    'deep_work'::public.block_type_enum,
    'scheduled'::public.block_status_enum
) ON CONFLICT (id) DO NOTHING;

-- Calendar events (Meeting constraint)
INSERT INTO public.calendar_events (id, user_id, google_event_id, title, start_at, end_at, source, is_chronos_created)
VALUES (
    'd0000000-0000-0000-0000-000000000002',
    '00000000-0000-0000-0000-000000000000',
    'g_call_urgent',
    'Urgent Client Call',
    NOW() + INTERVAL '4 hours 30 minutes',
    NOW() + INTERVAL '5 hours 30 minutes',
    'google',
    false
) ON CONFLICT (user_id, google_event_id) DO NOTHING;

-- Drift event
INSERT INTO public.drift_events (id, user_id, commitment_id, focus_block_id, drift_type, severity, description)
VALUES (
    'd0000000-0000-0000-0000-000000000003',
    '00000000-0000-0000-0000-000000000000',
    'd0000000-0000-0000-0000-000000000000',
    'd0000000-0000-0000-0000-000000000001',
    'new_event',
    'warning',
    'New client meeting invitation conflicts with scheduled code review focus block.'
) ON CONFLICT (id) DO NOTHING;
