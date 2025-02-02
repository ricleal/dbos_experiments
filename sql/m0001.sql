drop table if exists accesses;

drop table if exists users;

drop table if exists errors;

drop type if exists status;

drop table if exists random_users;

drop table if exists tasks;

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

insert into
    users (id, name, email)
values
    (
        '00000000-00000000-00000000-00000001',
        'Alice',
        'alice@foo.bar'
    ),
    (
        '00000000-00000000-00000000-00000002',
        'Bob',
        'bob@foo.bar'
    ),
    (
        '00000000-00000000-00000000-00000003',
        'Charlie',
        'charlie@foo.bar'
    ),
    (
        '00000000-00000000-00000000-00000004',
        'David',
        'david@foo.bar'
    ),
    (
        '00000000-00000000-00000000-00000005',
        'Eve',
        'eve@ex.co'
    );

insert into accesses (user_id, status)
values ('00000000-00000000-00000000-00000001', 'requested'),
       ('00000000-00000000-00000000-00000002', 'approved'),
       ('00000000-00000000-00000000-00000003', 'rejected'),
       ('00000000-00000000-00000000-00000004', 'canceled');

create table if not exists random_users (
    id uuid primary key,
    gender VARCHAR(255),
    title VARCHAR(255),
    first_name VARCHAR(255),
    last_name VARCHAR(255),
    street_number INTEGER,
    street_name VARCHAR(255),
    city VARCHAR(255),
    state VARCHAR(255),
    country VARCHAR(255),
    postcode VARCHAR(255),
    latitude double precision,
    longitude double precision,
    timezone_offset VARCHAR(255),
    timezone_description VARCHAR(255),
    email VARCHAR(255),
    uuid VARCHAR(255),
    username VARCHAR(255),
    password VARCHAR(255),
    salt VARCHAR(255),
    md5 VARCHAR(255),
    sha1 VARCHAR(255),
    sha256 VARCHAR(255),
    date_of_birth TIMESTAMP,
    age INTEGER,
    registered_at TIMESTAMP,
    phone VARCHAR(255),
    cell VARCHAR(255),
    id_name VARCHAR(255),
    id_value VARCHAR(255),
    picture_large VARCHAR(255),
    picture_medium VARCHAR(255),
    picture_thumbnail VARCHAR(255),
    nat VARCHAR(255)
);

create table if not exists tasks (
    id uuid primary key default gen_random_uuid(),
    title text null,
    data jsonb not null,
    created_at timestamp not null default now()
);