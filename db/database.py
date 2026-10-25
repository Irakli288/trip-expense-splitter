"""Подключение к базе данных SQLite проекта (ПР7).

База хранится в файле data/splitter.sqlite, структура таблиц
описана в sql/schema.sql. Пути строятся от корня проекта, поэтому
модуль работает при запуске из любого каталога.
"""

import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "splitter.sqlite"
SCHEMA_FILE = BASE_DIR / "sql" / "schema.sql"


def get_connection(db_path: Path | str | None = None) -> sqlite3.Connection:
    """Открыть соединение с базой и включить проверку внешних ключей.

    По умолчанию SQLite не проверяет, что внешний ключ ссылается
    на существующую запись, поэтому PRAGMA выполняется при каждом
    подключении.
    """
    conn = sqlite3.connect(db_path or DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def create_tables(conn: sqlite3.Connection) -> None:
    """Создать таблицы командами из sql/schema.sql."""
    conn.executescript(SCHEMA_FILE.read_text(encoding="utf-8"))
