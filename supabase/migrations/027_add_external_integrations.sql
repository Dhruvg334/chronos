create table if not exists public.integration_connections (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  provider text not null check (provider in ('google_calendar','gmail','github','notion','outlook_calendar','obsidian','microsoft_planner','mcp')),
  status text not null default 'disconnected' check (status in ('connected','degraded','expired','revoked','disconnected','error')),
  granted_scopes text[] not null default '{}',
  external_account_reference text,
  token_reference text,
  connected_at timestamptz,
  last_success_at timestamptz,
  last_error_at timestamptz,
  last_error_code text,
  sync_cursor text,
  sync_metadata jsonb not null default '{}',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (user_id, provider, external_account_reference),
  unique (id, user_id)
);

create table if not exists public.integration_items (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  connection_id uuid not null,
  provider text not null,
  external_id text not null,
  item_type text not null,
  title text not null,
  content_summary text not null default '',
  source_url text,
  occurred_at timestamptz,
  due_at timestamptz,
  project_id uuid,
  checksum text not null,
  metadata jsonb not null default '{}',
  synchronized_at timestamptz not null default now(),
  deleted_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint integration_items_connection_owner_fk foreign key (connection_id, user_id)
    references public.integration_connections(id, user_id) on delete cascade,
  constraint integration_items_project_owner_fk foreign key (project_id, user_id)
    references public.projects(id, user_id) on delete set null (project_id),
  unique (connection_id, external_id),
  unique (id, user_id)
);

create table if not exists public.integration_action_proposals (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  connection_id uuid not null,
  integration_item_id uuid,
  action_type text not null,
  target jsonb not null default '{}',
  safe_summary text not null,
  validated_payload jsonb not null default '{}',
  status text not null default 'pending' check (status in ('pending','approved','rejected','dismissed','expired')),
  approval_requirement text not null default 'explicit',
  idempotency_key text not null,
  created_at timestamptz not null default now(),
  resolved_at timestamptz,
  constraint integration_proposals_connection_owner_fk foreign key (connection_id, user_id)
    references public.integration_connections(id, user_id) on delete cascade,
  constraint integration_proposals_item_owner_fk foreign key (integration_item_id, user_id)
    references public.integration_items(id, user_id) on delete set null (integration_item_id),
  unique (user_id, idempotency_key),
  unique (id, user_id)
);

create table if not exists public.integration_audit_events (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  connection_id uuid,
  provider text not null,
  event_type text not null,
  outcome text not null,
  request_id text,
  workflow_id text,
  safe_metadata jsonb not null default '{}',
  created_at timestamptz not null default now(),
  constraint integration_audit_connection_owner_fk foreign key (connection_id, user_id)
    references public.integration_connections(id, user_id) on delete set null (connection_id)
);

create index if not exists integration_items_user_provider_time_idx on public.integration_items(user_id, provider, synchronized_at desc);
create index if not exists integration_items_project_idx on public.integration_items(user_id, project_id) where deleted_at is null;
create index if not exists integration_proposals_user_status_idx on public.integration_action_proposals(user_id, status, created_at desc);
create index if not exists integration_audit_user_time_idx on public.integration_audit_events(user_id, created_at desc);

alter table public.integration_connections enable row level security;
alter table public.integration_items enable row level security;
alter table public.integration_action_proposals enable row level security;
alter table public.integration_audit_events enable row level security;

create policy integration_connections_owner_read on public.integration_connections for select to authenticated using (auth.uid() = user_id);
create policy integration_items_owner_read on public.integration_items for select to authenticated using (auth.uid() = user_id);
create policy integration_proposals_owner_read on public.integration_action_proposals for select to authenticated using (auth.uid() = user_id);
create policy integration_audit_owner_read on public.integration_audit_events for select to authenticated using (auth.uid() = user_id);

revoke all on public.integration_connections, public.integration_items, public.integration_action_proposals, public.integration_audit_events from public, anon, authenticated;
grant select (id, user_id, provider, status, granted_scopes, external_account_reference, connected_at, last_success_at, last_error_at, last_error_code, created_at, updated_at)
  on public.integration_connections to authenticated;
grant select (id, user_id, connection_id, provider, external_id, item_type, title, content_summary, source_url, occurred_at, due_at, project_id, checksum, synchronized_at, deleted_at, created_at, updated_at)
  on public.integration_items to authenticated;
grant select (id, user_id, connection_id, integration_item_id, action_type, target, safe_summary, status, approval_requirement, created_at, resolved_at)
  on public.integration_action_proposals to authenticated;
grant select (id, user_id, connection_id, provider, event_type, outcome, request_id, workflow_id, safe_metadata, created_at)
  on public.integration_audit_events to authenticated;
grant all on public.integration_connections, public.integration_items, public.integration_action_proposals, public.integration_audit_events to service_role;

comment on column public.integration_connections.token_reference is 'Backend-only reference to Vault or provider credential storage; never a raw token.';
comment on column public.integration_items.metadata is 'Strictly allow-listed provider metadata; never an unrestricted provider payload.';
comment on table public.integration_action_proposals is 'Approval-first records; migration 027 adds no external-provider mutation executor.';

create or replace function public.approve_integration_proposal_transaction(
  p_user_id uuid, p_proposal_id uuid, p_action_type text, p_project_id uuid default null
) returns jsonb
language plpgsql security definer set search_path = pg_catalog
as $$
declare
  v_proposal public.integration_action_proposals%rowtype;
  v_item public.integration_items%rowtype;
  v_entity_id uuid;
begin
  if auth.uid() is not null and auth.uid() <> p_user_id then raise exception 'ownership_violation'; end if;
  select * into v_proposal from public.integration_action_proposals where id = p_proposal_id and user_id = p_user_id for update;
  if not found then raise exception 'proposal_not_found'; end if;
  if v_proposal.status = 'approved' then
    return pg_catalog.jsonb_build_object('status','approved','entity_id',v_proposal.validated_payload->>'approved_entity_id','idempotent_replay',true);
  end if;
  if v_proposal.status <> 'pending' then raise exception 'proposal_not_pending'; end if;
  select * into v_item from public.integration_items where id = v_proposal.integration_item_id and user_id = p_user_id;
  if not found then raise exception 'source_not_found'; end if;
  if p_project_id is not null and not exists(select 1 from public.projects where id=p_project_id and user_id=p_user_id) then raise exception 'project_not_found'; end if;
  if p_action_type in ('create_task','create_event') then
    insert into public.commitments(user_id,title,description,type,status,deadline_at,confidence_score,project_id)
    values(p_user_id, left(v_item.title,180), left(v_item.content_summary,2000), case when p_action_type='create_event' then 'event'::public.commitment_type else 'hard_deadline'::public.commitment_type end, 'inbox'::public.commitment_status, v_item.due_at, 0.6, p_project_id)
    returning id into v_entity_id;
  elsif p_action_type = 'create_outcome' then
    insert into public.outcomes(user_id,project_id,title,description,status,importance,confidence,completion_criteria,provenance)
    values(p_user_id,p_project_id,left(v_item.title,180),left(v_item.content_summary,1000),'uncertain',3,0.6,'Confirm the completed state before planning work.','integration:' || v_item.provider)
    returning id into v_entity_id;
  elsif p_action_type <> 'create_reference' then raise exception 'unsupported_action'; end if;
  update public.integration_action_proposals set action_type=p_action_type,status='approved',resolved_at=pg_catalog.now(),validated_payload=validated_payload || pg_catalog.jsonb_build_object('approved_entity_id',v_entity_id,'project_id',p_project_id) where id=p_proposal_id;
  insert into public.integration_audit_events(user_id,connection_id,provider,event_type,outcome,safe_metadata)
  values(p_user_id,v_item.connection_id,v_item.provider,'approval','approved',pg_catalog.jsonb_build_object('action_type',p_action_type));
  return pg_catalog.jsonb_build_object('status','approved','entity_id',v_entity_id,'idempotent_replay',false);
end;
$$;
revoke all on function public.approve_integration_proposal_transaction(uuid,uuid,text,uuid) from public, anon;
grant execute on function public.approve_integration_proposal_transaction(uuid,uuid,text,uuid) to authenticated, service_role;

-- Preserve the existing Vault token lifecycle while narrowing the definer boundary.
create or replace function public.set_google_tokens(p_user_id uuid,p_google_email text,p_access_token text,p_refresh_token text,p_token_uri text,p_client_id text,p_scopes text[],p_expires_at timestamptz)
returns void language plpgsql security definer set search_path=pg_catalog as $$
declare v_access uuid; v_refresh uuid; v_old_access uuid; v_old_refresh uuid;
begin
  select access_token_secret_id,refresh_token_secret_id into v_old_access,v_old_refresh from public.google_connections where user_id=p_user_id for update;
  if v_old_access is not null then perform vault.delete_secret(v_old_access); end if;
  select vault.create_secret(p_access_token,'google_access_token_'||p_user_id,'Google access token') into v_access;
  if p_refresh_token is not null and p_refresh_token<>'' then
    if v_old_refresh is not null then perform vault.delete_secret(v_old_refresh); end if;
    select vault.create_secret(p_refresh_token,'google_refresh_token_'||p_user_id,'Google refresh token') into v_refresh;
  else v_refresh:=v_old_refresh; end if;
  insert into public.google_connections(user_id,google_email,access_token_secret_id,refresh_token_secret_id,token_uri,client_id,scopes,expires_at)
  values(p_user_id,p_google_email,v_access,v_refresh,p_token_uri,p_client_id,p_scopes,p_expires_at)
  on conflict(user_id) do update set google_email=excluded.google_email,access_token_secret_id=excluded.access_token_secret_id,refresh_token_secret_id=excluded.refresh_token_secret_id,token_uri=excluded.token_uri,client_id=excluded.client_id,scopes=excluded.scopes,expires_at=excluded.expires_at,updated_at=pg_catalog.now();
end $$;

create or replace function public.get_decrypted_google_tokens(p_user_id uuid)
returns table(access_token text,refresh_token text,token_uri text,client_id text,scopes text[],expires_at timestamptz)
language sql security definer set search_path=pg_catalog as $$
  select va.secret,vr.secret,gc.token_uri,gc.client_id,gc.scopes,gc.expires_at from public.google_connections gc
  left join vault.decrypted_secrets va on va.id=gc.access_token_secret_id left join vault.decrypted_secrets vr on vr.id=gc.refresh_token_secret_id where gc.user_id=p_user_id
$$;

create or replace function public.delete_google_connection(p_user_id uuid)
returns void language plpgsql security definer set search_path=pg_catalog as $$
declare v_access uuid; v_refresh uuid;
begin
  select access_token_secret_id,refresh_token_secret_id into v_access,v_refresh from public.google_connections where user_id=p_user_id for update;
  if v_access is not null then perform vault.delete_secret(v_access); end if;
  if v_refresh is not null then perform vault.delete_secret(v_refresh); end if;
  delete from public.google_connections where user_id=p_user_id;
end $$;

revoke all on function public.set_google_tokens(uuid,text,text,text,text,text,text[],timestamptz), public.get_decrypted_google_tokens(uuid), public.delete_google_connection(uuid) from public, anon, authenticated;
grant execute on function public.set_google_tokens(uuid,text,text,text,text,text,text[],timestamptz), public.get_decrypted_google_tokens(uuid), public.delete_google_connection(uuid) to service_role;
