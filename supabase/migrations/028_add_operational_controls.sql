create table public.usage_counters (
  scope_key text not null,
  category text not null,
  window_start timestamptz not null,
  request_count integer not null default 0 check (request_count >= 0),
  updated_at timestamptz not null default now(),
  primary key (scope_key, category, window_start)
);

-- Vault token lifecycle compatibility: current Vault exposes the secrets table
-- but not a delete_secret function. Definer functions delete only selected IDs.
create or replace function public.set_google_tokens(p_user_id uuid,p_google_email text,p_access_token text,p_refresh_token text,p_token_uri text,p_client_id text,p_scopes text[],p_expires_at timestamptz)
returns void language plpgsql security definer set search_path=pg_catalog as $$
declare v_access uuid; v_refresh uuid; v_old_access uuid; v_old_refresh uuid;
begin
  select access_token_secret_id,refresh_token_secret_id into v_old_access,v_old_refresh from public.google_connections where user_id=p_user_id for update;
  if v_old_access is not null then delete from vault.secrets where id=v_old_access; end if;
  select vault.create_secret(p_access_token,'google_access_token_'||p_user_id,'Google access token') into v_access;
  if p_refresh_token is not null and p_refresh_token<>'' then
    if v_old_refresh is not null then delete from vault.secrets where id=v_old_refresh; end if;
    select vault.create_secret(p_refresh_token,'google_refresh_token_'||p_user_id,'Google refresh token') into v_refresh;
  else v_refresh:=v_old_refresh; end if;
  insert into public.google_connections(user_id,google_email,access_token_secret_id,refresh_token_secret_id,token_uri,client_id,scopes,expires_at)
  values(p_user_id,p_google_email,v_access,v_refresh,p_token_uri,p_client_id,p_scopes,p_expires_at)
  on conflict(user_id) do update set google_email=excluded.google_email,access_token_secret_id=excluded.access_token_secret_id,refresh_token_secret_id=excluded.refresh_token_secret_id,token_uri=excluded.token_uri,client_id=excluded.client_id,scopes=excluded.scopes,expires_at=excluded.expires_at,updated_at=pg_catalog.now();
end $$;

create or replace function public.delete_google_connection(p_user_id uuid)
returns void language plpgsql security definer set search_path=pg_catalog as $$
declare v_access uuid; v_refresh uuid;
begin
  select access_token_secret_id,refresh_token_secret_id into v_access,v_refresh from public.google_connections where user_id=p_user_id for update;
  if v_access is not null then delete from vault.secrets where id=v_access; end if;
  if v_refresh is not null then delete from vault.secrets where id=v_refresh; end if;
  delete from public.google_connections where user_id=p_user_id;
end $$;
revoke all on function public.set_google_tokens(uuid,text,text,text,text,text,text[],timestamptz),public.delete_google_connection(uuid) from public,anon,authenticated;
grant execute on function public.set_google_tokens(uuid,text,text,text,text,text,text[],timestamptz),public.delete_google_connection(uuid) to service_role;

create table public.operational_audit_events (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references auth.users(id) on delete cascade,
  event_type text not null,
  outcome text not null,
  failure_code text,
  request_id text,
  workflow_id text,
  safe_metadata jsonb not null default '{}',
  created_at timestamptz not null default now()
);

create index operational_audit_user_time_idx on public.operational_audit_events(user_id, created_at desc);
alter table public.usage_counters enable row level security;
alter table public.operational_audit_events enable row level security;
create policy operational_audit_owner_read on public.operational_audit_events for select to authenticated using (auth.uid() = user_id);
revoke all on public.usage_counters, public.operational_audit_events from public, anon, authenticated;
grant select (id,user_id,event_type,outcome,failure_code,request_id,workflow_id,safe_metadata,created_at) on public.operational_audit_events to authenticated;
grant all on public.usage_counters, public.operational_audit_events to service_role;

create or replace function public.consume_usage_budget(
  p_user_id uuid, p_category text, p_user_limit integer, p_global_limit integer, p_units integer default 1
) returns jsonb language plpgsql security definer set search_path=pg_catalog as $$
declare v_window timestamptz := pg_catalog.date_trunc('hour', pg_catalog.now()); v_user integer; v_global integer; v_retry integer;
begin
  if p_units < 1 or p_user_limit < 1 or p_global_limit < p_user_limit then raise exception 'invalid_limit'; end if;
  perform pg_catalog.pg_advisory_xact_lock(pg_catalog.hashtext(p_category || ':' || v_window::text));
  select request_count into v_user from public.usage_counters where scope_key='user:'||p_user_id and category=p_category and window_start=v_window;
  select request_count into v_global from public.usage_counters where scope_key='global' and category=p_category and window_start=v_window;
  v_user:=coalesce(v_user,0); v_global:=coalesce(v_global,0);
  v_retry:=greatest(1,pg_catalog.date_part('epoch',v_window + interval '1 hour' - pg_catalog.now())::integer);
  if v_user + p_units > p_user_limit or v_global + p_units > p_global_limit then
    insert into public.operational_audit_events(user_id,event_type,outcome,failure_code,safe_metadata)
    values(p_user_id,'usage_budget','denied','rate_limited',pg_catalog.jsonb_build_object('category',p_category,'retry_after_seconds',v_retry));
    return pg_catalog.jsonb_build_object('allowed',false,'retry_after_seconds',v_retry,'user_remaining',greatest(0,p_user_limit-v_user),'global_remaining',greatest(0,p_global_limit-v_global));
  end if;
  insert into public.usage_counters(scope_key,category,window_start,request_count) values('user:'||p_user_id,p_category,v_window,p_units)
    on conflict(scope_key,category,window_start) do update set request_count=public.usage_counters.request_count+excluded.request_count,updated_at=pg_catalog.now();
  insert into public.usage_counters(scope_key,category,window_start,request_count) values('global',p_category,v_window,p_units)
    on conflict(scope_key,category,window_start) do update set request_count=public.usage_counters.request_count+excluded.request_count,updated_at=pg_catalog.now();
  return pg_catalog.jsonb_build_object('allowed',true,'retry_after_seconds',0,'user_remaining',p_user_limit-v_user-p_units,'global_remaining',p_global_limit-v_global-p_units);
end $$;

create or replace function public.account_data_inventory(p_user_id uuid)
returns jsonb language plpgsql security definer set search_path=pg_catalog as $$
begin
  if auth.uid() is not null and auth.uid()<>p_user_id then raise exception 'ownership_violation'; end if;
  return pg_catalog.jsonb_build_object(
    'projects',(select count(*) from public.projects where user_id=p_user_id),
    'outcomes',(select count(*) from public.outcomes where user_id=p_user_id),
    'routines',(select count(*) from public.routines where user_id=p_user_id),
    'commitments',(select count(*) from public.commitments where user_id=p_user_id),
    'memories',(select count(*) from public.memory_items where user_id=p_user_id),
    'knowledge_sources',(select count(*) from public.knowledge_sources where user_id=p_user_id),
    'knowledge_chunks',(select count(*) from public.knowledge_chunks where user_id=p_user_id),
    'integration_connections',(select count(*) from public.integration_connections where user_id=p_user_id),
    'integration_items',(select count(*) from public.integration_items where user_id=p_user_id),
    'workflow_traces',(select count(*) from public.agent_trace_events where user_id=p_user_id),
    'audit_events',(select count(*) from public.integration_audit_events where user_id=p_user_id)+(select count(*) from public.operational_audit_events where user_id=p_user_id)
  );
end $$;

create or replace function public.delete_knowledge_source_transaction(p_user_id uuid,p_source_id uuid)
returns jsonb language plpgsql security definer set search_path=pg_catalog as $$
declare v_chunks integer;
begin
  if auth.uid() is not null and auth.uid()<>p_user_id then raise exception 'ownership_violation'; end if;
  if not exists(select 1 from public.knowledge_sources where id=p_source_id and user_id=p_user_id) then raise exception 'source_not_found'; end if;
  select count(*) into v_chunks from public.knowledge_chunks where source_id=p_source_id and user_id=p_user_id;
  delete from public.knowledge_sources where id=p_source_id and user_id=p_user_id;
  insert into public.operational_audit_events(user_id,event_type,outcome,safe_metadata) values(p_user_id,'knowledge_source_delete','succeeded',pg_catalog.jsonb_build_object('chunk_count',v_chunks));
  return pg_catalog.jsonb_build_object('status','deleted','chunk_count',v_chunks);
end $$;

create or replace function public.delete_account_transaction(p_user_id uuid,p_confirmation text)
returns jsonb language plpgsql security definer set search_path=pg_catalog as $$
declare v_inventory jsonb; v_access uuid; v_refresh uuid;
begin
  if p_confirmation <> 'DELETE MY ACCOUNT' then raise exception 'confirmation_required'; end if;
  if auth.uid() is not null and auth.uid()<>p_user_id then raise exception 'ownership_violation'; end if;
  v_inventory:=public.account_data_inventory(p_user_id);
  select access_token_secret_id,refresh_token_secret_id into v_access,v_refresh from public.google_connections where user_id=p_user_id for update;
  if v_access is not null then delete from vault.secrets where id=v_access; end if;
  if v_refresh is not null then delete from vault.secrets where id=v_refresh; end if;
  delete from public.google_connections where user_id=p_user_id;
  delete from public.user_profiles where id=p_user_id;
  delete from auth.users where id=p_user_id;
  return pg_catalog.jsonb_build_object('status','deleted','inventory',v_inventory);
end $$;

create or replace function public.purge_expired_operational_data(p_trace_days integer default 90,p_audit_days integer default 365)
returns jsonb language plpgsql security definer set search_path=pg_catalog as $$
declare v_traces integer; v_integration integer; v_operational integer; v_usage integer;
begin
  if p_trace_days < 7 or p_audit_days < 30 then raise exception 'retention_too_short'; end if;
  delete from public.agent_trace_events where created_at < pg_catalog.now()-pg_catalog.make_interval(days=>p_trace_days); get diagnostics v_traces=row_count;
  delete from public.integration_audit_events where created_at < pg_catalog.now()-pg_catalog.make_interval(days=>p_audit_days); get diagnostics v_integration=row_count;
  delete from public.operational_audit_events where created_at < pg_catalog.now()-pg_catalog.make_interval(days=>p_audit_days); get diagnostics v_operational=row_count;
  delete from public.usage_counters where window_start < pg_catalog.now()-interval '48 hours'; get diagnostics v_usage=row_count;
  return pg_catalog.jsonb_build_object('trace_events',v_traces,'integration_audits',v_integration,'operational_audits',v_operational,'usage_windows',v_usage);
end $$;

revoke all on function public.consume_usage_budget(uuid,text,integer,integer,integer),public.account_data_inventory(uuid),public.delete_knowledge_source_transaction(uuid,uuid),public.delete_account_transaction(uuid,text),public.purge_expired_operational_data(integer,integer) from public,anon;
grant execute on function public.account_data_inventory(uuid),public.delete_knowledge_source_transaction(uuid,uuid) to authenticated,service_role;
grant execute on function public.consume_usage_budget(uuid,text,integer,integer,integer),public.delete_account_transaction(uuid,text),public.purge_expired_operational_data(integer,integer) to service_role;

-- Harden older immutable SECURITY DEFINER functions without rewriting their bodies.
alter function public.handle_new_user() set search_path=pg_catalog;
alter function public.approve_intake_transaction(uuid,uuid,text,jsonb) set search_path=pg_catalog;
alter function public.complete_focus_transaction(uuid,uuid,uuid,text,integer,text,integer,integer,double precision,public.risk_level_type,text,text) set search_path=pg_catalog;
alter function public.approve_recovery_transaction(uuid,uuid,text,uuid) set search_path=pg_catalog;
