# Supabase Schema Migration Plan

This directory holds the PostgreSQL migration files. They must be executed in the exact order specified by the prefix numerical values to preserve foreign key constraints.

## Migration Files Sequence

1. `001_create_user_profiles.sql`
   - Defines autonomy level enums and user preferences tables.
   - Installs the auto-creation trigger linking `auth.users` additions to user profiles.
2. `002_create_google_connections.sql`
   - Establishes the decoupled credentials table for external calendar connections.
3. `003_create_commitments.sql`
   - Establishes the core time commitments and indexes.
4. `004_create_tasks.sql`
   - Establishes detailed breakdowns (Next actions, starter steps).
5. `005_create_time_spines.sql`
   - Maps out Structured timelines and gates.
6. `006_create_calendar_events.sql`
   - Synced events database w/ `UNIQUE(user_id, google_event_id)` compound keys.
7. `007_create_focus_blocks.sql`
   - Stores scheduled calendar capacity blocks.
8. `008_create_drift_events.sql`
   - Stores plan mismatch records.
9. `009_create_agent_runs.sql`
   - Tracks LangGraph pipeline checkpoints.
10. `010_create_agent_trace_events.sql`
    - Stores backend real-time logging trace records.
11. `011_create_agent_proposed_actions.sql`
    - Decision Dock approvals collection queue.
12. `012_create_reflections.sql`
    - Stores block feedback metrics.
13. `013_create_user_memory.sql`
    - Stores overrun factors and planning coefficients.

## System-Wide Trigger functions
All migration scripts will incorporate:
- Row-Level Security policies restricting reads/writes using `USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id)`.
- Timestamp triggers executing:
```sql
CREATE OR REPLACE TRIGGER update_table_modtime
    BEFORE UPDATE ON table_name
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
```
