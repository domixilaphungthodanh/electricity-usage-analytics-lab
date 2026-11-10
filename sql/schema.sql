CREATE TABLE rooms (
    room_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);
CREATE TABLE readings (
    room_id INTEGER NOT NULL REFERENCES rooms(room_id),
    hour_start TEXT NOT NULL CHECK(
        hour_start >= '2026-04-01 00:00:00' AND hour_start < '2026-05-01 00:00:00'
        AND strftime('%Y-%m-%d %H:00:00', hour_start, '+0 seconds') IS hour_start
    ),
    wh INTEGER NOT NULL CHECK(typeof(wh) = 'integer' AND wh BETWEEN 0 AND 1000000000),
    PRIMARY KEY (room_id, hour_start)
);
CREATE TABLE metadata (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
