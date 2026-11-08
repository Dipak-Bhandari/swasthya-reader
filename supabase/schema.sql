-- Run in the Supabase SQL editor.
-- Plain tables only for now. Add pgvector later only if you need cross-report search.

create extension if not exists "pgcrypto";

create table if not exists reports (
  id uuid primary key default gen_random_uuid(),
  created_at timestamptz not null default now(),
  extracted_json jsonb not null,
  nepali_summary text not null,
  tips_json jsonb not null default '{}'::jsonb,
  see_doctor_soon boolean not null default false,
  audio_url text
);

create table if not exists chat_messages (
  id bigserial primary key,
  report_id uuid not null references reports(id) on delete cascade,
  role text not null check (role in ('user', 'assistant')),
  content text not null,
  created_at timestamptz not null default now()
);

create index if not exists chat_messages_report_idx on chat_messages (report_id, created_at);

-- The backend uses the service key, which bypasses RLS. Turn RLS on so the anon key can't read anything.
alter table reports enable row level security;
alter table chat_messages enable row level security;

notify pgrst, 'reload schema';
