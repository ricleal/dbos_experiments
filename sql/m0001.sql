drop table if exists accesses;

drop table if exists users;

drop table if exists errors;

drop type if exists status;

drop table if exists random_users;

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
    );

insert into
    users (id, name, email)
values
    (
        '00000000-00000000-00000000-00000002',
        'Bob',
        'bob@foo.bar'
    );

insert into
    users (id, name, email)
values
    (
        '00000000-00000000-00000000-00000003',
        'Charlie',
        'charlie@foo.bar'
    );

insert into
    users (id, name, email)
values
    (
        '00000000-00000000-00000000-00000004',
        'David',
        'david@foo.bar'
    );

insert into
    users (id, name, email)
values
    (
        '00000000-00000000-00000000-00000005',
        'Eve',
        'eve@ex.co'
    );

-- {
--     "cell": "L21 X70-3497",
--     "dob": {
--         "age": 71,
--         "date": "1953-06-10T10:46:57.964Z"
--     },
--     "email": "amelia.knight@example.com",
--     "gender": "female",
--     "id": {
--         "name": "SIN",
--         "value": "862989829"
--     },
--     "location": {
--         "city": "Windsor",
--         "coordinates": {
--             "latitude": "-64.9294",
--             "longitude": "62.6672"
--         },
--         "country": "Canada",
--         "postcode": "D6P 1C6",
--         "state": "Saskatchewan",
--         "street": {
--             "name": "Vimy St",
--             "number": 3837
--         },
--         "timezone": {
--             "description": "Bombay, Calcutta, Madras, New Delhi",
--             "offset": "+5:30"
--         }
--     },
--     "login": {
--         "md5": "dcd031836a8bd780b2d5343eb2a52fe7",
--         "password": "ciccio",
--         "salt": "AcJWf2XE",
--         "sha1": "611c60639cbea4fd8aa41aedb3d1aa6c11ce27ff",
--         "sha256": "496be9e2e0759b6fe1bc6937937b8bfb422f9d2be28846bff02522e84145f4e3",
--         "username": "whitepeacock226",
--         "uuid": "17eb6ffe-d609-4c1d-873e-b22a8a785694"
--     },
--     "name": {
--         "first": "Amelia",
--         "last": "Knight",
--         "title": "Ms"
--     },
--     "nat": "CA",
--     "phone": "Q45 I45-2901",
--     "picture": {
--         "large": "https://randomuser.me/api/portraits/women/54.jpg",
--         "medium": "https://randomuser.me/api/portraits/med/women/54.jpg",
--         "thumbnail": "https://randomuser.me/api/portraits/thumb/women/54.jpg"
--     },
--     "registered": {
--         "age": 10,
--         "date": "2014-10-30T17:21:48.640Z"
--     }
-- }
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
    latitude DECIMAL(10, 8),
    longitude DECIMAL(10, 8),
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