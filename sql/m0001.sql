drop table if exists accesses;
drop table if exists users;
drop table if exists errors;
drop type if exists status;

create type status as enum ('requested', 'approved', 'rejected', 'canceled');

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
    status status not null default 'requested',
    created_at timestamp not null default now(),
    updated_at timestamp not null default now()
);

create table if not exists errors (
    id uuid primary key default gen_random_uuid(),
    message text not null,
    created_at timestamp not null default now()
);

insert into users (id, name, email) values ('00000000-00000000-00000000-00000001', 'Alice', 'alice@foo.bar');
insert into users (id, name, email) values ('00000000-00000000-00000000-00000002', 'Bob', 'bob@foo.bar');
insert into users (id, name, email) values ('00000000-00000000-00000000-00000003', 'Charlie', 'charlie@foo.bar');
insert into users (id, name, email) values ('00000000-00000000-00000000-00000004', 'David', 'david@foo.bar');
insert into users (id, name, email) values ('00000000-00000000-00000000-00000005', 'Eve', 'eve@ex.co');
