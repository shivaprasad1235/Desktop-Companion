CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT
);

INSERT OR IGNORE INTO settings (key, value) VALUES ('character_pack', 'robobuddy');
INSERT OR IGNORE INTO settings (key, value) VALUES ('size', '64');
INSERT OR IGNORE INTO settings (key, value) VALUES ('movement_speed', '1.0');
INSERT OR IGNORE INTO settings (key, value) VALUES ('greeting_enabled', '1');
INSERT OR IGNORE INTO settings (key, value) VALUES ('auto_start', '0');
INSERT OR IGNORE INTO settings (key, value) VALUES ('animation_fps', '12');
INSERT OR IGNORE INTO settings (key, value) VALUES ('opacity', '1.0');
INSERT OR IGNORE INTO settings (key, value) VALUES ('click_through', '0');
INSERT OR IGNORE INTO settings (key, value) VALUES ('always_on_top', '1');
INSERT OR IGNORE INTO settings (key, value) VALUES ('language', 'English');
INSERT OR IGNORE INTO settings (key, value) VALUES ('mute', '0');
INSERT OR IGNORE INTO settings (key, value) VALUES ('personality', 'Friendly');
