-- Memória de conhecimento do KAWA-AI.
-- Aplicar apenas em um projeto Supabase controlado pelo proprietário.

create table if not exists public.kawa_knowledge (
  id uuid primary key default gen_random_uuid(),
  title text not null check (char_length(title) between 1 and 180),
  content text not null check (char_length(content) > 0),
  source text not null default 'kawa_ai',
  created_at timestamptz not null default now()
);

create index if not exists kawa_knowledge_created_at_idx
  on public.kawa_knowledge (created_at desc);

alter table public.kawa_knowledge enable row level security;

-- A tabela não recebe políticas públicas. O KAWA-AI usa uma credencial local
-- de servidor guardada no cofre do sistema, sem gravá-la no Git, diário ou logs.

-- Correção aplicada no projeto existente após confirmação do proprietário.
revoke execute on function public.rls_auto_enable() from anon, authenticated, public;
