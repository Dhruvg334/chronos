-- 014_grant_api_role_privileges.sql
-- Grants required for Supabase/PostgREST API roles.
-- RLS policies still control row-level access for anon/authenticated users.
-- service_role is backend-only and must never be exposed to frontend.

grant usage on schema public to anon, authenticated, service_role;

grant select, insert, update, delete on table public.user_profiles to authenticated, service_role;
grant select, insert, update, delete on table public.google_connections to authenticated, service_role;
grant select, insert, update, delete on table public.commitments to authenticated, service_role;
grant select, insert, update, delete on table public.tasks to authenticated, service_role;
grant select, insert, update, delete on table public.time_spines to authenticated, service_role;
grant select, insert, update, delete on table public.calendar_events to authenticated, service_role;
grant select, insert, update, delete on table public.focus_blocks to authenticated, service_role;
grant select, insert, update, delete on table public.drift_events to authenticated, service_role;
grant select, insert, update, delete on table public.agent_runs to authenticated, service_role;
grant select, insert, update, delete on table public.agent_trace_events to authenticated, service_role;
grant select, insert, update, delete on table public.agent_proposed_actions to authenticated, service_role;
grant select, insert, update, delete on table public.reflections to authenticated, service_role;
grant select, insert, update, delete on table public.user_memory to authenticated, service_role;

-- Optional read-only anon access is intentionally not granted for app data.
-- ChronOS user data must not be publicly readable.

-- Future-proof grants for tables/sequences created later in public schema.
alter default privileges in schema public
grant select, insert, update, delete on tables to authenticated, service_role;

alter default privileges in schema public
grant usage, select on sequences to authenticated, service_role;