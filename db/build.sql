CREATE TABLE IF NOT EXISTS bot_version(
    version VARCHAR(20) PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS bot_log_channel(
    server_id INT PRIMARY KEY,
    log_channel_id INT
);

CREATE TABLE IF NOT EXISTS bot_archive_role(
    server_id INT PRIMARY KEY,
    archive_role_id INT
);

CREATE TABLE IF NOT EXISTS bot_song_library(
    id INT PRIMARY KEY,
    artist VARCHAR(200),
    song_title VARCHAR(200),
    album VARCHAR(200),
    length_in_seconds int
);