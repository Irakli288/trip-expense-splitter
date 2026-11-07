"""Показывает, что лежит в старой базе data/splitter.sqlite.

Запускать из корня проекта перед переносом данных:

    python -m db.inspect_source_db

Для каждой таблицы выводит столбцы и число записей. Скрипт только
читает базу и ничего в ней не меняет.
"""

import sqlite3
from contextlib import closing

from db.database import DB_PATH


def main(db_path=DB_PATH):
    if not db_path.exists():
        raise FileNotFoundError(f"Старая база не найдена: {db_path}")
    with closing(sqlite3.connect(db_path)) as conn:
        conn.row_factory = sqlite3.Row
        tables = conn.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
                AND name NOT LIKE 'sqlite_%'
            ORDER BY name
            """
        ).fetchall()
        for (table_name,) in tables:
            print(f"\nТаблица: {table_name}")
            for column in conn.execute(f'PRAGMA table_info("{table_name}")'):
                print(
                    f"  {column['name']}: {column['type']}, "
                    f"NOT NULL={column['notnull']}, "
                    f"PRIMARY KEY={column['pk']}"
                )
            count = conn.execute(
                f'SELECT COUNT(*) FROM "{table_name}"'
            ).fetchone()[0]
            print(f"Записей: {count}")


if __name__ == "__main__":
    main()
