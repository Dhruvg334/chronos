---
name: supabase-security
description: Review or implement ChronOS Supabase schemas, forward migrations, RLS policies, grants, Vault OAuth storage, authenticated queries, and frontend/backend credential separation. Use for any database, auth, policy, Vault, or Supabase adapter change.
---

# Supabase Security

## Required inputs

- Existing migrations and target data behavior
- Table ownership and authenticated operations
- Current RLS, grants, functions, and token storage

## Workflow

1. Read migrations in order and inspect affected policies/functions/grants.
2. Confirm whether a migration has been applied; never edit applied history.
3. Design an additive forward migration with rollback considerations.
4. Scope user-owned access through `auth.uid()` and validated backend identity.
5. Keep service-role and OAuth token material backend-only.
6. Test policies locally only as an opt-in integration workflow.

## Checks

- RLS is enabled for every user-owned table.
- `SECURITY DEFINER` functions pin search paths and minimize grants.
- Vault tokens are never selected by browser roles or logged.
- Demo data is static/isolated and anonymous users cannot access workspaces.

## Commands

Run `rg -n "ENABLE ROW LEVEL SECURITY|CREATE POLICY|SECURITY DEFINER|GRANT" supabase/migrations`; optionally `supabase start --ignore-health-check`, `supabase db reset`, `supabase status`, then `supabase stop`.

## Expected output

Provide policy findings, migration SQL if authorized, role matrix, data risk, and verification.

## Stop conditions

Stop before destructive data changes, applied-migration edits, broad anonymous grants, plaintext token storage, or moving service-role keys to frontend code.
