-- Run once in the Supabase SQL editor.
create extension if not exists "pgcrypto";

create table if not exists sheets (
  id uuid primary key default gen_random_uuid(),
  title text not null default 'Untitled sheet',
  created_at timestamptz not null default now()
);

create table if not exists columns (
  id uuid primary key default gen_random_uuid(),
  sheet_id uuid not null references sheets(id) on delete cascade,
  position int not null default 0,
  question text not null,
  created_at timestamptz not null default now()
);

create table if not exists rows (
  id uuid primary key default gen_random_uuid(),
  sheet_id uuid not null references sheets(id) on delete cascade,
  position int not null default 0,
  entity text not null,
  created_at timestamptz not null default now()
);

create table if not exists cells (
  id uuid primary key default gen_random_uuid(),
  sheet_id uuid not null references sheets(id) on delete cascade,
  row_id uuid not null references rows(id) on delete cascade,
  column_id uuid not null references columns(id) on delete cascade,
  status text not null default 'idle',
  answer text,
  detail text,
  confidence text,
  sources jsonb not null default '[]',
  error text,
  attempts int not null default 0,
  queued_at timestamptz,
  locked_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (row_id, column_id)
);

create table if not exists cell_steps (
  id uuid primary key default gen_random_uuid(),
  cell_id uuid not null references cells(id) on delete cascade,
  idx int not null,
  node text not null,
  summary text not null,
  data jsonb not null default '{}',
  created_at timestamptz not null default now()
);

create index if not exists cells_sheet_idx on cells(sheet_id);
-- Partial index keeps worker polling O(queued) no matter how many cells exist.
create index if not exists cells_claim_idx on cells(queued_at) where status in ('queued', 'running');
create index if not exists steps_cell_idx on cell_steps(cell_id, idx);

-- The API connects with the service key (bypasses RLS); lock out anon access.
alter table sheets enable row level security;
alter table columns enable row level security;
alter table rows enable row level security;
alter table cells enable row level security;
alter table cell_steps enable row level security;

-- Atomic job claiming: safe with many API/worker instances (SKIP LOCKED).
-- Also reclaims cells whose worker died (running, but lock older than p_stale_seconds).
create or replace function claim_cells(p_limit int, p_stale_seconds int)
returns setof cells
language sql
as $$
  update cells set status = 'running', locked_at = now(), updated_at = now(),
                   attempts = attempts + 1
  where id in (
    select id from cells
    where (status = 'queued' and (queued_at is null or queued_at <= now()))
       or (status = 'running' and locked_at < now() - make_interval(secs => p_stale_seconds))
    order by queued_at nulls last
    for update skip locked
    limit p_limit
  )
  returning *;
$$;
