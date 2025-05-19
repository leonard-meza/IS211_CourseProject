drop table if exists users;
create table users (
    id integer primary key autoincrement,
    username text unique not null,
    password text not null
);

drop table if exists categories;
create table categories (
    id integer primary key autoincrement,
    name text unique not null
);

drop table if exists posts;
create table posts (
    id integer primary key autoincrement,
    title text not null,
    content text not null,
    created timestamp not null default current_timestamp,
    published integer not null default 1,
    user_id integer not null,
    category_id integer not null,
    foreign key (user_id) references users(id),
    foreign key (category_id) references categories(id)
)

