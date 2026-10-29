"""Подключение к базе данных SQLite.

Сама база лежит в data/splitter.sqlite, а таблицы описаны
в sql/schema.sql. Пути считаются от корня проекта, так что
неважно, из какой папки запускать код.
"""

import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "splitter.sqlite"
SCHEMA_FILE = BASE_DIR / "sql" / "schema.sql"


def get_connection(db_path: Path | str | None = None) -> sqlite3.Connection:
    """Открывает базу и включает проверку внешних ключей.

    SQLite сам по себе не следит, что внешний ключ указывает
    на существующую запись. Поэтому PRAGMA приходится включать
    заново при каждом подключении.
    """
    conn = sqlite3.connect(db_path or DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def create_tables(conn: sqlite3.Connection) -> None:
    """Создает таблицы по командам из sql/schema.sql."""
    conn.executescript(SCHEMA_FILE.read_text(encoding="utf-8"))
