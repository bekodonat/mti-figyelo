import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Generator, List, Dict, Any, Optional

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from config.settings import DB_PATH, OUTLETS_CONFIG_PATH


SCHEMA_SQL = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS outlets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    slug TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    domain TEXT NOT NULL,
    rss_url TEXT NOT NULL,
    active BOOLEAN DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS mti_news (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guid TEXT UNIQUE NOT NULL,
    url TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    lead TEXT,
    content_raw TEXT NOT NULL,
    published_at DATETIME NOT NULL,
    scraped_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    is_hot BOOLEAN DEFAULT 1,
    word_count INTEGER
);

CREATE TABLE IF NOT EXISTS articles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    outlet_id INTEGER NOT NULL,
    url TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    lead TEXT,
    content_raw TEXT NOT NULL,
    published_at DATETIME,
    scraped_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    has_mti_citation BOOLEAN DEFAULT 0,
    citation_excerpt TEXT,
    word_count INTEGER,
    FOREIGN KEY (outlet_id) REFERENCES outlets (id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS matches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    mti_id INTEGER NOT NULL,
    article_id INTEGER NOT NULL,
    similarity_score REAL NOT NULL,
    latency_minutes INTEGER,
    matched_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(mti_id, article_id),
    FOREIGN KEY (mti_id) REFERENCES mti_news (id) ON DELETE CASCADE,
    FOREIGN KEY (article_id) REFERENCES articles (id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_outlets_slug ON outlets (slug);
CREATE INDEX IF NOT EXISTS idx_mti_is_hot ON mti_news (is_hot);
CREATE INDEX IF NOT EXISTS idx_mti_published_at ON mti_news (published_at);
CREATE INDEX IF NOT EXISTS idx_articles_url ON articles (url);
CREATE INDEX IF NOT EXISTS idx_articles_outlet_id ON articles (outlet_id);
CREATE INDEX IF NOT EXISTS idx_articles_published_at ON articles (published_at);
CREATE INDEX IF NOT EXISTS idx_articles_has_mti ON articles (has_mti_citation);
CREATE INDEX IF NOT EXISTS idx_matches_mti_id ON matches (mti_id);
CREATE INDEX IF NOT EXISTS idx_matches_article_id ON matches (article_id);
"""


@contextmanager
def get_db() -> Generator[sqlite3.Connection, None, None]:
    """Provide a transactional database connection."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    """Initialize database tables and indexes."""
    with get_db() as conn:
        conn.executescript(SCHEMA_SQL)
    print(f"Adatbázis sikeresen inicializálva: {DB_PATH}")


def seed_outlets() -> int:
    """Load or update outlets from outlets.json into the database."""
    if not OUTLETS_CONFIG_PATH.exists():
        raise FileNotFoundError(f"Nem található az outlets konfiguráció: {OUTLETS_CONFIG_PATH}")

    with open(OUTLETS_CONFIG_PATH, "r", encoding="utf-8") as f:
        outlets_data: List[Dict[str, Any]] = json.load(f)

    inserted_or_updated = 0
    with get_db() as conn:
        for outlet in outlets_data:
            conn.execute(
                """
                INSERT INTO outlets (slug, name, domain, rss_url, active)
                VALUES (:slug, :name, :domain, :rss_url, :active)
                ON CONFLICT(slug) DO UPDATE SET
                    name = excluded.name,
                    domain = excluded.domain,
                    rss_url = excluded.rss_url,
                    active = excluded.active;
                """,
                outlet,
            )
            inserted_or_updated += 1

    print(f"Sikeresen rögzítve/frissítve {inserted_or_updated} médium az adatbázisban.")
    return inserted_or_updated


def get_active_outlets() -> List[sqlite3.Row]:
    """Retrieve all active outlets."""
    with get_db() as conn:
        cursor = conn.execute("SELECT * FROM outlets WHERE active = 1 ORDER BY name ASC")
        return cursor.fetchall()


def get_existing_article_urls(urls: List[str]) -> set:
    """Check which URLs from a given list already exist in the database."""
    if not urls:
        return set()
    with get_db() as conn:
        placeholders = ",".join("?" for _ in urls)
        cursor = conn.execute(
            f"SELECT url FROM articles WHERE url IN ({placeholders})",
            urls,
        )
        return {row["url"] for row in cursor.fetchall()}


def update_mti_hot_status(hot_window_hours: int = 12) -> int:
    """Set is_hot = 0 for MTI news older than hot_window_hours based on scraped_at."""
    with get_db() as conn:
        cursor = conn.execute(
            f"""
            UPDATE mti_news 
            SET is_hot = 0 
            WHERE is_hot = 1 
              AND datetime(scraped_at) < datetime('now', '-{hot_window_hours} hours');
            """
        )
        affected = cursor.rowcount
    return affected


if __name__ == "__main__":
    init_db()
    seed_outlets()
