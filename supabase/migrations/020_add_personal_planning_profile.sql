-- Migration: 020_add_personal_planning_profile.sql
-- Description: Explicit, user-owned availability settings for deterministic planning.

ALTER TABLE public.user_profiles
    ADD COLUMN available_weekdays SMALLINT[] NOT NULL DEFAULT ARRAY[0,1,2,3,4,5,6]::SMALLINT[],
    ADD COLUMN working_start_time TIME NOT NULL DEFAULT '09:00',
    ADD COLUMN working_end_time TIME NOT NULL DEFAULT '17:00',
    ADD COLUMN daily_focus_limit_minutes INTEGER NOT NULL DEFAULT 240,
    ADD COLUMN default_focus_duration_minutes INTEGER NOT NULL DEFAULT 45,
    ADD COLUMN minimum_transition_buffer_minutes INTEGER NOT NULL DEFAULT 10,
    ADD COLUMN minimum_daily_unscheduled_buffer_minutes INTEGER NOT NULL DEFAULT 60,
    ADD COLUMN protected_interval_start TIME,
    ADD COLUMN protected_interval_end TIME,
    ADD COLUMN quick_task_threshold_minutes INTEGER NOT NULL DEFAULT 5;

-- Carry forward the compatible portions of the legacy JSON preferences.
UPDATE public.user_profiles
SET
    working_start_time = CASE
        WHEN working_hours_json->>'start' ~ '^([01][0-9]|2[0-3]):[0-5][0-9]$'
            THEN (working_hours_json->>'start')::TIME
        ELSE working_start_time
    END,
    working_end_time = CASE
        WHEN working_hours_json->>'end' ~ '^([01][0-9]|2[0-3]):[0-5][0-9]$'
            THEN (working_hours_json->>'end')::TIME
        ELSE working_end_time
    END,
    default_focus_duration_minutes = CASE
        WHEN focus_preferences_json->>'deep_work_duration' ~ '^[0-9]+$'
            THEN LEAST(180, GREATEST(5, (focus_preferences_json->>'deep_work_duration')::INTEGER))
        ELSE default_focus_duration_minutes
    END;

ALTER TABLE public.user_profiles
    ADD CONSTRAINT user_profiles_available_weekdays_valid CHECK (
        cardinality(available_weekdays) BETWEEN 1 AND 7
        AND available_weekdays <@ ARRAY[0,1,2,3,4,5,6]::SMALLINT[]
    ),
    ADD CONSTRAINT user_profiles_work_window_valid CHECK (working_start_time < working_end_time),
    ADD CONSTRAINT user_profiles_focus_limit_valid CHECK (daily_focus_limit_minutes BETWEEN 15 AND 1440),
    ADD CONSTRAINT user_profiles_focus_duration_valid CHECK (default_focus_duration_minutes BETWEEN 5 AND 180),
    ADD CONSTRAINT user_profiles_transition_buffer_valid CHECK (minimum_transition_buffer_minutes BETWEEN 0 AND 120),
    ADD CONSTRAINT user_profiles_daily_buffer_valid CHECK (minimum_daily_unscheduled_buffer_minutes BETWEEN 0 AND 720),
    ADD CONSTRAINT user_profiles_quick_threshold_valid CHECK (quick_task_threshold_minutes BETWEEN 1 AND 60),
    ADD CONSTRAINT user_profiles_protected_interval_pair CHECK (
        (protected_interval_start IS NULL AND protected_interval_end IS NULL)
        OR (
            protected_interval_start IS NOT NULL
            AND protected_interval_end IS NOT NULL
            AND protected_interval_start < protected_interval_end
            AND protected_interval_start >= working_start_time
            AND protected_interval_end <= working_end_time
        )
    );

COMMENT ON COLUMN public.user_profiles.available_weekdays IS 'Python weekday numbers: Monday=0 through Sunday=6.';
