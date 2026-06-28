-- 1. Create Autonomy Level Enum
CREATE TYPE public.autonomy_level_type AS ENUM (
    'suggest', 
    'ask', 
    'act_low_risk', 
    'rescue_intervention', 
    'external_write'
);

-- 2. Create User Profiles Table
CREATE TABLE public.user_profiles (
    id UUID PRIMARY KEY, -- references auth.users(id) - set by trigger/auth
    display_name TEXT,
    timezone TEXT DEFAULT 'UTC' NOT NULL,
    working_hours_json JSONB DEFAULT '{"start": "09:00", "end": "17:00", "days": [1,2,3,4,5]}'::jsonb NOT NULL,
    focus_preferences_json JSONB DEFAULT '{"deep_work_duration": 90, "shallow_work_duration": 30, "default_buffer_percent": 15}'::jsonb NOT NULL,
    autonomy_level public.autonomy_level_type DEFAULT 'ask'::public.autonomy_level_type NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL
);

-- 3. Create updated_at automated timestamp updater function
CREATE OR REPLACE FUNCTION public.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Hook trigger to user_profiles
CREATE TRIGGER update_user_profiles_modtime
    BEFORE UPDATE ON public.user_profiles
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

-- 4. Create trigger function to provision user profiles automatically on auth signup
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.user_profiles (id, display_name, timezone, working_hours_json, focus_preferences_json, autonomy_level)
    VALUES (
        new.id,
        COALESCE(new.raw_user_meta_data->>'display_name', 'ChronOS User'),
        'UTC',
        '{"start": "09:00", "end": "17:00", "days": [1,2,3,4,5]}'::jsonb,
        '{"deep_work_duration": 90, "shallow_work_duration": 30, "default_buffer_percent": 15}'::jsonb,
        'ask'::public.autonomy_level_type
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- 5. Enable Row Level Security (RLS)
ALTER TABLE public.user_profiles ENABLE ROW LEVEL SECURITY;

-- 6. Create Explicit RLS Policies
CREATE POLICY "Users can select their own profile"
    ON public.user_profiles FOR SELECT
    USING (auth.uid() = id);

CREATE POLICY "Users can insert their own profile"
    ON public.user_profiles FOR INSERT
    WITH CHECK (auth.uid() = id);

CREATE POLICY "Users can update their own profile"
    ON public.user_profiles FOR UPDATE
    USING (auth.uid() = id)
    WITH CHECK (auth.uid() = id);

CREATE POLICY "Users can delete their own profile"
    ON public.user_profiles FOR DELETE
    USING (auth.uid() = id);

-- 7. Hook trigger to auth.users table
-- We check if trigger exists before creating it (useful in environments with resets)
CREATE OR REPLACE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();
