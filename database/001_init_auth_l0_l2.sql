-- CharPick base schema for Supabase/PostgreSQL
-- Scope: auth + L0 + L1 + L2

begin;

create extension if not exists pgcrypto;
create extension if not exists vector;

-- Generate readable IDs like u_xxx, b_xxx, ch_xxx.
create or replace function public.gen_prefixed_id(prefix text)
returns text
language sql
as $$
  select prefix || '_' || substr(replace(gen_random_uuid()::text, '-', ''), 1, 16);
$$;

create or replace function public.set_updated_at()
returns trigger
language plpgsql
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

-- 1) users
create table if not exists public.users (
  id text primary key default public.gen_prefixed_id('u'),
  username text not null unique,
  email text unique,
  password_hash text not null,
  status text not null default 'active' check (status in ('active', 'disabled')),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create trigger trg_users_updated_at
before update on public.users
for each row execute function public.set_updated_at();

-- 2) auth_sessions
create table if not exists public.auth_sessions (
  id text primary key default public.gen_prefixed_id('s'),
  user_id text not null references public.users(id) on delete cascade,
  access_token_jti text not null unique,
  refresh_token_hash text not null,
  expires_at timestamptz not null,
  revoked_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists idx_auth_sessions_user_id on public.auth_sessions(user_id);
create index if not exists idx_auth_sessions_expires_at on public.auth_sessions(expires_at);

create trigger trg_auth_sessions_updated_at
before update on public.auth_sessions
for each row execute function public.set_updated_at();

-- 3) books (L0)
create table if not exists public.books (
  id text primary key default public.gen_prefixed_id('b'),
  user_id text not null references public.users(id) on delete cascade,
  title text not null,
  author text,
  source_type text not null check (source_type in ('epub', 'txt', 'pdf', 'image')),
  language text not null default 'zh-CN',
  status text not null default 'pending' check (status in ('pending', 'parsing', 'parsed', 'failed')),
  cover_url text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists idx_books_user_id on public.books(user_id);
create index if not exists idx_books_status on public.books(status);

create trigger trg_books_updated_at
before update on public.books
for each row execute function public.set_updated_at();

-- 4) source_files (L0)
create table if not exists public.source_files (
  id text primary key default public.gen_prefixed_id('sf'),
  user_id text not null references public.users(id) on delete cascade,
  book_id text not null references public.books(id) on delete cascade,
  file_name text not null,
  file_url text not null,
  file_hash text not null,
  mime_type text,
  raw_text_url text,
  ocr_text_url text,
  parse_status text not null default 'pending' check (parse_status in ('pending', 'running', 'parsed', 'failed')),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (book_id, file_hash)
);

create index if not exists idx_source_files_user_id on public.source_files(user_id);
create index if not exists idx_source_files_book_id on public.source_files(book_id);

create trigger trg_source_files_updated_at
before update on public.source_files
for each row execute function public.set_updated_at();

-- 5) chapters (L1)
create table if not exists public.chapters (
  id text primary key default public.gen_prefixed_id('ch'),
  user_id text not null references public.users(id) on delete cascade,
  book_id text not null references public.books(id) on delete cascade,
  chapter_no integer not null,
  chapter_title text,
  chapter_range text,
  content_text text not null,
  word_count integer,
  source_file_id text references public.source_files(id) on delete set null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (book_id, chapter_no)
);

create index if not exists idx_chapters_user_id on public.chapters(user_id);
create index if not exists idx_chapters_book_id on public.chapters(book_id);

create trigger trg_chapters_updated_at
before update on public.chapters
for each row execute function public.set_updated_at();

-- 6) chapter_extractions (L2)
create table if not exists public.chapter_extractions (
  id text primary key default public.gen_prefixed_id('ex'),
  user_id text not null references public.users(id) on delete cascade,
  book_id text not null references public.books(id) on delete cascade,
  chapter_id text not null references public.chapters(id) on delete cascade,
  extractor_type text not null check (extractor_type in ('character', 'plot', 'item', 'location', 'summary', 'full')),
  extraction_json jsonb not null,
  embedding_vector vector(1536),
  prompt_version text,
  model_name text,
  confidence numeric(5,4),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (chapter_id, extractor_type)
);

create index if not exists idx_chapter_extractions_user_id on public.chapter_extractions(user_id);
create index if not exists idx_chapter_extractions_book_id on public.chapter_extractions(book_id);
create index if not exists idx_chapter_extractions_chapter_id on public.chapter_extractions(chapter_id);
create index if not exists idx_chapter_extractions_json_gin on public.chapter_extractions using gin(extraction_json);

create trigger trg_chapter_extractions_updated_at
before update on public.chapter_extractions
for each row execute function public.set_updated_at();

commit;
