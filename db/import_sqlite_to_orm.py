"""Переносит данные из старой базы ПР7 в базу Django.

Старая база data/splitter.sqlite остается как есть и служит источником.
Django работает с db.sqlite3 (настройка DATABASES), таблицы в ней
создает команда migrate. Порядок запуска из корня проекта:

    python manage.py migrate
    python -m db.import_sqlite_to_orm

Номера записей сохраняются, поэтому связи между поездками, участниками
и расходами не теряются. Запускать можно повторно: совпадающие записи
обновятся, а не продублируются.
"""

import os
import sqlite3
from contextlib import closing
from datetime import date
from decimal import Decimal

from db.database import DB_PATH as SOURCE_DB


def read_source(source_db):
    """Читает все строки старой базы в словарь списков."""
    if not os.path.exists(source_db):
        raise FileNotFoundError(f"Старая база не найдена: {source_db}")
    with closing(sqlite3.connect(source_db)) as conn:
        conn.row_factory = sqlite3.Row
        return {
            "trips": conn.execute(
                "SELECT id, name, start_date, end_date, budget "
                "FROM trips ORDER BY id"
            ).fetchall(),
            "participants": conn.execute(
                "SELECT id, trip_id, name FROM participants ORDER BY id"
            ).fetchall(),
            "expenses": conn.execute(
                "SELECT id, trip_id, title, amount, category, "
                "expense_date, payer_id FROM expenses ORDER BY id"
            ).fetchall(),
            "shares": conn.execute(
                "SELECT expense_id, participant_id FROM expense_shares "
                "ORDER BY expense_id, participant_id"
            ).fetchall(),
        }


def money(value):
    """Сумма из REAL старой базы в Decimal с копейками."""
    if value is None:
        return None
    return Decimal(str(value)).quantize(Decimal("0.01"))


def transfer(source_db=SOURCE_DB):
    """Переносит записи через ORM и возвращает, сколько чего в базе Django.

    Сначала поездки, потом участники, потом расходы: каждая следующая
    таблица ссылается на предыдущие. Все делается в одной транзакции,
    так что при ошибке в базе Django не останется половины данных.
    """
    # Модели импортируем здесь: к этому моменту Django уже настроен.
    from django.db import transaction

    from expenses.models import Expense
    from trips.models import Participant, Trip

    rows = read_source(source_db)
    shares = {}
    for row in rows["shares"]:
        shares.setdefault(row["expense_id"], []).append(row["participant_id"])

    with transaction.atomic():
        for row in rows["trips"]:
            Trip.objects.update_or_create(
                pk=row["id"],
                defaults={
                    "name": row["name"],
                    "start_date": date.fromisoformat(row["start_date"]),
                    "end_date": date.fromisoformat(row["end_date"]),
                    "budget": money(row["budget"]),
                },
            )
        for row in rows["participants"]:
            Participant.objects.update_or_create(
                pk=row["id"],
                defaults={"trip_id": row["trip_id"], "name": row["name"]},
            )
        for row in rows["expenses"]:
            expense, _ = Expense.objects.update_or_create(
                pk=row["id"],
                defaults={
                    "trip_id": row["trip_id"],
                    "title": row["title"],
                    "amount": money(row["amount"]),
                    "category": row["category"],
                    "expense_date": date.fromisoformat(row["expense_date"]),
                    "payer_id": row["payer_id"],
                },
            )
            # set() заменяет список участников расхода целиком.
            expense.split_between.set(shares.get(row["id"], []))

    return {
        "trips": Trip.objects.count(),
        "participants": Participant.objects.count(),
        "expenses": Expense.objects.count(),
    }


def main():
    import django

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "splitter.settings")
    django.setup()
    counts = transfer()
    print("Данные перенесены в базу Django.")
    print(f"Поездок: {counts['trips']}")
    print(f"Участников: {counts['participants']}")
    print(f"Расходов: {counts['expenses']}")


if __name__ == "__main__":
    main()
