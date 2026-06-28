# Supabase Database Verification Script

This document provides a complete SQL script to verify the ChronOS database schema, triggers, constraints, and Row Level Security (RLS) policies.

Copy and run these tests in the **Supabase SQL Editor** to confirm correct database behavior.

---

## 1. Setup Mock Test Users

To simulate authenticated users (User A and User B), we will temporarily create entries in Supabase Auth's `auth.users` table:

```sql
-- Create mock users in auth schema
INSERT INTO auth.users (id, email)
VALUES 
('aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', 'usera@chronos.os'),
('bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb', 'userb@chronos.os')
ON CONFLICT (id) DO NOTHING;
```

---

## 2. Test Verification Scenarios

### Test 1: Profile Auto-Creation Trigger
Verify that adding a user to `auth.users` automatically provisions their profile in `public.user_profiles` with default parameters.

```sql
-- Check if handle_new_user() trigger provisioned profiles automatically
SELECT id, display_name, timezone, autonomy_level 
FROM public.user_profiles 
WHERE id IN ('aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', 'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb');

-- ASSERTION: Exactly 2 rows should return with 'ChronOS User' names and autonomy level set to 'ask'.
```

---

### Test 2: Auto-Update of `updated_at` Column
Verify that modifying user preferences changes the `updated_at` timestamp automatically.

```sql
-- Check original timestamp
SELECT updated_at FROM public.user_profiles WHERE id = 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa';

-- Perform an update
UPDATE public.user_profiles 
SET timezone = 'Asia/Kolkata' 
WHERE id = 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa';

-- Check updated timestamp
SELECT updated_at FROM public.user_profiles WHERE id = 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa';

-- ASSERTION: The second timestamp must be greater than the first one.
```

---

### Test 3: RLS Isolation (SELECT Access)
Verify that User A cannot read commitments belonging to User B.

```sql
-- Insert a commitment as User B
INSERT INTO public.commitments (id, user_id, title, status)
VALUES ('b1111111-1111-1111-1111-111111111111', 'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb', 'User B Secrets', 'active');

-- Simulate session as User A
SET LOCAL request.jwt.claim.sub = 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa';

-- Attempt to read User B commitments
SELECT * FROM public.commitments WHERE user_id = 'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb';

-- ASSERTION: Must return 0 rows (RLS SELECT active).
```

---

### Test 4: RLS Isolation (INSERT Access)
Verify that User A cannot insert records scoped to User B's `user_id`.

```sql
-- Simulate session as User A
SET LOCAL request.jwt.claim.sub = 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa';

-- Attempt to insert a commitment under User B's ID
INSERT INTO public.commitments (user_id, title)
VALUES ('bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb', 'User A Hacking User B');

-- ASSERTION: Must fail with an error: "new row violates row-level security policy for table commitments".
```

---

### Test 5: Proposed Actions Table Constraints
Verify that the approvals table correctly validates `proposed_action_type` and `proposed_action_status` enums.

```sql
-- Setup mock agent run
INSERT INTO public.agent_runs (id, user_id, run_type, status, input_json)
VALUES ('99999999-9999-9999-9999-999999999999', 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', 'replan', 'completed', '{}');

-- Insert valid pending proposed action
INSERT INTO public.agent_proposed_actions (user_id, agent_run_id, action_type, status, payload_json, explanation)
VALUES (
    'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
    '99999999-9999-9999-9999-999999999999',
    'calendar_move'::public.proposed_action_type,
    'pending'::public.proposed_action_status,
    '{"event_id": "g123", "new_start": "2026-06-25T10:00:00Z"}'::jsonb,
    'Shifting deep focus block'
);

-- Check status
SELECT action_type, status FROM public.agent_proposed_actions WHERE user_id = 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa';

-- ASSERTION: Inserts successfully. Attempting to set status to 'invalid_status' must fail with type validation errors.
```

---

### Test 6: Calendar Events Compound Unique Constraint
Verify that different users can share the same `google_event_id` in the cache without collisions, but a single user cannot have duplicate event IDs.

```sql
-- Insert event for User A
INSERT INTO public.calendar_events (user_id, google_event_id, title, start_at, end_at)
VALUES ('aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', 'shared_google_id_123', 'Sync Meeting', NOW(), NOW() + INTERVAL '1 hour')
ON CONFLICT DO NOTHING;

-- Insert event for User B with the SAME google_event_id
INSERT INTO public.calendar_events (user_id, google_event_id, title, start_at, end_at)
VALUES ('bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb', 'shared_google_id_123', 'Sync Meeting', NOW(), NOW() + INTERVAL '1 hour')
ON CONFLICT DO NOTHING;

-- ASSERTION: Both events insert successfully (Compound UNIQUE validates).

-- Try to insert duplicate event for User A again
INSERT INTO public.calendar_events (user_id, google_event_id, title, start_at, end_at)
VALUES ('aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', 'shared_google_id_123', 'Sync Meeting Dup', NOW(), NOW() + INTERVAL '1 hour');

-- ASSERTION: Must fail with unique constraint violation: "duplicate key value violates unique constraint".
```

---

## 3. Cleanup Test Data

Once testing is completed, run this script to clean up the test logs:

```sql
DELETE FROM auth.users WHERE id IN ('aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', 'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb');
-- Cascade delete will automatically clean public.user_profiles, commitments, proposed actions, and events.
```
