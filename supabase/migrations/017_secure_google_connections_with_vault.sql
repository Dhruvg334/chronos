-- Migration: 017_secure_google_connections_with_vault.sql
-- Description: Move OAuth tokens to Supabase Vault and expose service_role only RPCs

-- 1. Enable vault extension
CREATE EXTENSION IF NOT EXISTS "supabase_vault" CASCADE;

-- 2. Clear existing plaintext tokens (Dev/Hackathon acceptable)
TRUNCATE TABLE public.google_connections;

-- 3. Modify schema to remove plaintext and add Vault references
ALTER TABLE public.google_connections 
  DROP COLUMN access_token,
  DROP COLUMN refresh_token,
  ADD COLUMN access_token_secret_id UUID,
  ADD COLUMN refresh_token_secret_id UUID;

-- Ensure Vault schema is completely inaccessible to public/authenticated
REVOKE ALL ON SCHEMA vault FROM PUBLIC, authenticated;

-- 4. Create secure RPC to store tokens
CREATE OR REPLACE FUNCTION public.set_google_tokens(
    p_user_id UUID,
    p_google_email TEXT,
    p_access_token TEXT,
    p_refresh_token TEXT,
    p_token_uri TEXT,
    p_client_id TEXT,
    p_scopes TEXT[],
    p_expires_at TIMESTAMP WITH TIME ZONE
) RETURNS void AS $$
DECLARE
    v_access_secret_id UUID;
    v_refresh_secret_id UUID;
    v_existing_access_id UUID;
    v_existing_refresh_id UUID;
BEGIN
    -- Look up existing connection if any. Keep the refresh token only when Google
    -- does not return a new one during access-token refresh.
    SELECT access_token_secret_id, refresh_token_secret_id
    INTO v_existing_access_id, v_existing_refresh_id
    FROM public.google_connections
    WHERE user_id = p_user_id;

    -- Prevent stale access-token secrets from accumulating in Vault.
    IF v_existing_access_id IS NOT NULL THEN
        PERFORM vault.delete_secret(v_existing_access_id);
    END IF;

    -- Store the new access token in Vault.
    SELECT vault.create_secret(p_access_token, 'google_access_token_' || p_user_id, 'Google access token')
    INTO v_access_secret_id;

    -- Handle refresh token. If Google returns a new one, replace the old Vault
    -- secret. If not, preserve the existing refresh-token secret reference.
    IF p_refresh_token IS NOT NULL AND p_refresh_token <> '' THEN
        IF v_existing_refresh_id IS NOT NULL THEN
            PERFORM vault.delete_secret(v_existing_refresh_id);
        END IF;
        SELECT vault.create_secret(p_refresh_token, 'google_refresh_token_' || p_user_id, 'Google refresh token')
        INTO v_refresh_secret_id;
    ELSE
        v_refresh_secret_id := v_existing_refresh_id;
    END IF;

    -- Upsert connection record
    INSERT INTO public.google_connections (
        user_id, google_email, access_token_secret_id, refresh_token_secret_id, 
        token_uri, client_id, scopes, expires_at
    )
    VALUES (
        p_user_id, p_google_email, v_access_secret_id, v_refresh_secret_id, 
        p_token_uri, p_client_id, p_scopes, p_expires_at
    )
    ON CONFLICT (user_id) DO UPDATE SET
        google_email = EXCLUDED.google_email,
        access_token_secret_id = EXCLUDED.access_token_secret_id,
        refresh_token_secret_id = EXCLUDED.refresh_token_secret_id,
        token_uri = EXCLUDED.token_uri,
        client_id = EXCLUDED.client_id,
        scopes = EXCLUDED.scopes,
        expires_at = EXCLUDED.expires_at,
        updated_at = NOW();
END;
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_temp;

REVOKE ALL ON FUNCTION public.set_google_tokens FROM PUBLIC, authenticated;
GRANT EXECUTE ON FUNCTION public.set_google_tokens TO service_role;


-- 5. Create secure RPC to read tokens
CREATE OR REPLACE FUNCTION public.get_decrypted_google_tokens(p_user_id UUID)
RETURNS TABLE(
    access_token TEXT,
    refresh_token TEXT,
    token_uri TEXT,
    client_id TEXT,
    scopes TEXT[],
    expires_at TIMESTAMP WITH TIME ZONE
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        va.secret AS access_token,
        vr.secret AS refresh_token,
        gc.token_uri,
        gc.client_id,
        gc.scopes,
        gc.expires_at
    FROM public.google_connections gc
    LEFT JOIN vault.decrypted_secrets va ON va.id = gc.access_token_secret_id
    LEFT JOIN vault.decrypted_secrets vr ON vr.id = gc.refresh_token_secret_id
    WHERE gc.user_id = p_user_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_temp;

REVOKE ALL ON FUNCTION public.get_decrypted_google_tokens FROM PUBLIC, authenticated;
GRANT EXECUTE ON FUNCTION public.get_decrypted_google_tokens TO service_role;


-- 6. Create secure RPC to delete tokens
CREATE OR REPLACE FUNCTION public.delete_google_connection(p_user_id UUID)
RETURNS void AS $$
DECLARE
    v_access_id UUID;
    v_refresh_id UUID;
BEGIN
    SELECT access_token_secret_id, refresh_token_secret_id 
    INTO v_access_id, v_refresh_id
    FROM public.google_connections
    WHERE user_id = p_user_id;

    IF v_access_id IS NOT NULL THEN
        PERFORM vault.delete_secret(v_access_id);
    END IF;

    IF v_refresh_id IS NOT NULL THEN
        PERFORM vault.delete_secret(v_refresh_id);
    END IF;

    DELETE FROM public.google_connections WHERE user_id = p_user_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_temp;

REVOKE ALL ON FUNCTION public.delete_google_connection FROM PUBLIC, authenticated;
GRANT EXECUTE ON FUNCTION public.delete_google_connection TO service_role;
