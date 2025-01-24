
create table if not exists users (
    id uuid primary key default gen_random_uuid(),
    name text not null,
    email text not null unique,
    created_at timestamp not null default now(),
    updated_at timestamp not null default now()
);

create table if not exists accesses (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null references users (id),
    created_at timestamp not null default now(),
    updated_at timestamp not null default now(),
    foreign key (user_id) references users (id)
);
