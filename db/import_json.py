"""Перенос данных проекта из JSON-файлов в базу SQLite (ПР7).

Запуск из корня проекта:

    python -m db.import_json

Скрипт создает таблицы (если их еще нет), очищает их и заново
заполняет записями из data/trips.json, data/participants.json
и data/expenses.json, поэтому его можно запускать повторно.
"""

import json
from pathlib import Path

from db.database import BASE_DIR, create_tables, get_connection

TRIPS_FILE = BASE_DIR / "data" / "trips.json"
PARTICIPANTS_FILE = BASE_DIR / "data" / "participants.json"
EXPENSES_FILE = BASE_DIR / "data" / "expenses.json"


def load_json(filename: Path) -> list[dict]:
    """Прочитать список записей из JSON-файла."""
    with open(filename, encoding="utf-8") as file:
        return json.load(file)


def clear_tables(conn) -> None:
    """Удалить старые записи: сначала зависимые таблицы, потом главные."""
    conn.execute("DELETE FROM expense_shares")
    conn.execute("DELETE FROM expenses")
    conn.execute("DELETE FROM participants")
    conn.execute("DELETE FROM trips")


def import_trips(conn) -> None:
    """Перенести поездки; бюджет 0 сохраняется как NULL (не задан)."""
    trips = load_json(TRIPS_FILE)
    conn.executemany(
        """
        INSERT INTO trips (id, name, start_date, end_date, budget)
        VALUES (?, ?, ?, ?, ?)
        """,
        [
            (
                trip["id"],
                trip["name"],
                trip["start_date"],
                trip["end_date"],
                trip["budget"] or None,
            )
            for trip in trips
        ],
    )


def import_participants(conn) -> None:
    """Перенести участников поездок."""
    participants = load_json(PARTICIPANTS_FILE)
    conn.executemany(
        """
        INSERT INTO participants (id, trip_id, name)
        VALUES (?, ?, ?)
        """,
        [
            (item["id"], item["trip_id"], item["name"])
            for item in participants
        ],
    )


def import_expenses(conn) -> None:
    """Перенести расходы и список участников каждого расхода.

    Поле split_between из JSON превращается в записи таблицы
    expense_shares: одна запись на каждого участника расхода.
    """
    expenses = load_json(EXPENSES_FILE)
    conn.executemany(
        """
        INSERT INTO expenses (
            id, trip_id, title, amount, category, expense_date, payer_id
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (
                item["id"],
                item["trip_id"],
                item["title"],
                item["amount"],
                item["category"],
                item["date"],
                item["payer_id"],
            )
            for item in expenses
        ],
    )
    conn.executemany(
        """
        INSERT INTO expense_shares (expense_id, participant_id)
        VALUES (?, ?)
        """,
        [
            (item["id"], participant_id)
            for item in expenses
            for participant_id in sorted(set(item["split_between"]))
        ],
    )


def main(db_path: Path | str | None = None) -> None:
    """Создать таблицы и перенести в них все данные JSON."""
    conn = get_connection(db_path)
    try:
        create_tables(conn)
        clear_tables(conn)
        import_trips(conn)
        import_participants(conn)
        import_expenses(conn)
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    main()
    print("Данные перенесены из JSON в базу SQLite")
