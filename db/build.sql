CREATE TABLE IF NOT EXISTS bot_version(
    version VARCHAR(20) PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS bot_log_channel(
    server_id TEXT PRIMARY KEY,
    log_channel_id TEXT
);

CREATE TABLE IF NOT EXISTS bot_archive_role(
    server_id TEXT PRIMARY KEY,
    archive_role_id TEXT
);

CREATE TABLE IF NOT EXISTS bot_song_library(
    id INT PRIMARY KEY,
    artist VARCHAR(200),
    song_title VARCHAR(200),
    album VARCHAR(200),
    length_in_seconds INT,
    song_order INT DEFAULT -1
);

CREATE TABLE IF NOT EXISTS bot_word_blacklist(
    id INT PRIMARY KEY,
    server_id TEXT,
    word VARCHAR(50)
);