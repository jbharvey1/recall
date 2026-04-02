import sqlite3

_SCHEMA = """
CREATE TABLE IF NOT EXISTS reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    path TEXT NOT NULL,
    title TEXT NOT NULL,
    topic TEXT NOT NULL,
    thread TEXT,
    parent_id INTEGER REFERENCES reports(id),
    date TEXT NOT NULL,
    sources TEXT DEFAULT '[]',
    word_count INTEGER DEFAULT 0,
    image_count INTEGER DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS report_tags (
    report_id INTEGER NOT NULL REFERENCES reports(id) ON DELETE CASCADE,
    tag_id INTEGER NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
    PRIMARY KEY (report_id, tag_id)
);

CREATE INDEX IF NOT EXISTS idx_reports_thread ON reports(thread);
CREATE INDEX IF NOT EXISTS idx_reports_date ON reports(date);
"""


def get_connection(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: str) -> None:
    conn = get_connection(db_path)
    conn.executescript(_SCHEMA)
    conn.commit()
    conn.close()
