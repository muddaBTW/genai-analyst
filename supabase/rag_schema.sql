-- Run once in Supabase SQL Editor. The backend's secret key is the only role
-- permitted to read/write uploaded row data.
create extension if not exists vector;

create table if not exists public.rag_datasets (
  id uuid primary key,
  summary text not null,
  row_count integer not null,
  created_at timestamptz not null default now()
);

create table if not exists public.rag_dataset_rows (
  id bigint generated always as identity primary key,
  dataset_id uuid not null references public.rag_datasets(id) on delete cascade,
  row_index integer not null,
  content text not null,
  row_data jsonb not null,
  embedding vector(768) not null,
  unique(dataset_id, row_index)
);

alter table public.rag_datasets enable row level security;
alter table public.rag_dataset_rows enable row level security;
revoke all on public.rag_datasets, public.rag_dataset_rows from anon, authenticated;
grant select, insert, update, delete on public.rag_datasets, public.rag_dataset_rows to service_role;
grant usage, select on sequence public.rag_dataset_rows_id_seq to service_role;

create index if not exists rag_rows_dataset_id_idx on public.rag_dataset_rows(dataset_id);
create index if not exists rag_rows_embedding_hnsw_idx on public.rag_dataset_rows using hnsw (embedding vector_cosine_ops);

create or replace function public.match_dataset_rows(
  query_embedding vector(768), match_dataset_id uuid, match_count integer default 5
)
returns table(row_index integer, text text, row jsonb, score float)
language sql stable
as $$
  select row_index, content as text, row_data as row, 1 - (embedding <=> query_embedding) as score
  from public.rag_dataset_rows
  where dataset_id = match_dataset_id
  order by embedding <=> query_embedding
  limit match_count;
$$;

grant execute on function public.match_dataset_rows(vector, uuid, integer) to service_role;
