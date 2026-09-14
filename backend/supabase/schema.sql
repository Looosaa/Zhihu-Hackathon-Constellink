create extension if not exists pgcrypto;

create table if not exists learning_spaces (
  id uuid primary key default gen_random_uuid(),
  client_id text not null,
  topic text not null,
  level text not null check (level in ('beginner', 'starter', 'experienced')),
  goal text not null check (goal in ('understand', 'project', 'interview')),
  daily_minutes integer not null check (daily_minutes in (15, 30, 60, 90)),
  status text not null default 'created'
    check (status in ('created', 'analyzing', 'ready', 'failed')),
  error_message text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists sources (
  id uuid primary key default gen_random_uuid(),
  learning_space_id uuid not null references learning_spaces(id) on delete cascade,
  source_key text not null,
  provider text not null check (provider in ('zhihu', 'demo')),
  content_type text not null default 'answer',
  title text not null,
  author_name text not null,
  author_badge text,
  source_url text not null,
  excerpt text not null,
  published_at timestamptz,
  engagement jsonb not null default '{}'::jsonb,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  unique (learning_space_id, source_key)
);

create table if not exists analyses (
  id uuid primary key default gen_random_uuid(),
  learning_space_id uuid not null unique references learning_spaces(id) on delete cascade,
  overview text not null,
  consensus jsonb not null default '[]'::jsonb,
  disagreements jsonb not null default '[]'::jsonb,
  concepts jsonb not null default '[]'::jsonb,
  edges jsonb not null default '[]'::jsonb,
  source_summaries jsonb not null default '[]'::jsonb,
  warnings jsonb not null default '[]'::jsonb,
  model_name text,
  prompt_version text not null default 'v1',
  created_at timestamptz not null default now()
);

create table if not exists study_plans (
  id uuid primary key default gen_random_uuid(),
  learning_space_id uuid not null unique references learning_spaces(id) on delete cascade,
  strategy text not null,
  days jsonb not null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists quizzes (
  id uuid primary key default gen_random_uuid(),
  learning_space_id uuid not null references learning_spaces(id) on delete cascade,
  concept_id text,
  question text not null,
  reference_answer text not null,
  rubric jsonb not null default '[]'::jsonb,
  source_keys jsonb not null default '[]'::jsonb,
  created_at timestamptz not null default now()
);

create table if not exists quiz_attempts (
  id uuid primary key default gen_random_uuid(),
  quiz_id uuid not null references quizzes(id) on delete cascade,
  client_id text not null,
  answer text not null,
  score integer check (score between 0 and 100),
  strengths jsonb not null default '[]'::jsonb,
  improvements jsonb not null default '[]'::jsonb,
  next_step text,
  created_at timestamptz not null default now()
);

create index if not exists idx_spaces_client on learning_spaces(client_id, created_at desc);
create index if not exists idx_sources_space on sources(learning_space_id);
create index if not exists idx_quizzes_space on quizzes(learning_space_id);
create index if not exists idx_attempts_quiz on quiz_attempts(quiz_id, created_at desc);

alter table learning_spaces enable row level security;
alter table sources enable row level security;
alter table analyses enable row level security;
alter table study_plans enable row level security;
alter table quizzes enable row level security;
alter table quiz_attempts enable row level security;

-- Only the backend uses the service role key; no browser policies are intentionally created.
