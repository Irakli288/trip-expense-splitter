import sqlite3
from datetime import date

from django.shortcuts import render

from db.database import get_connection
from models import Expense, Participant, Settlement, Trip
from models.settlement import get_settlement_status

# Запрос 12 из sql/queries.sql: поездки с итогами и долей потраченного бюджета.
TRIPS_QUERY = """
    SELECT
        trips.id,
        trips.name,
        strftime('%d.%m.%Y', trips.start_date) AS start_date_ru,
        strftime('%d.%m.%Y', trips.end_date) AS end_date_ru,
        CAST(julianday(trips.end_date) - julianday(trips.start_date)
             AS INTEGER) + 1 AS duration,
        trips.budget,
        (SELECT COUNT(*)
         FROM participants
         WHERE participants.trip_id = trips.id) AS participants_count,
        COUNT(expenses.id) AS expenses_count,
        COALESCE(SUM(expenses.amount), 0) AS total,
        CASE
            WHEN trips.budget IS NULL THEN 'none'
            WHEN COALESCE(SUM(expenses.amount), 0) > trips.budget THEN 'over'
            WHEN COALESCE(SUM(expenses.amount), 0) >= trips.budget * 0.8
                THEN 'warning'
            ELSE 'ok'
        END AS budget_level
    FROM trips
    LEFT JOIN expenses
        ON expenses.trip_id = trips.id
    GROUP BY trips.id
    ORDER BY trips.start_date;
"""

# Запрос 13: одна поездка с итогами и состоянием бюджета.
TRIP_QUERY = """
    SELECT
        trips.id,
        trips.name,
        strftime('%d.%m.%Y', trips.start_date) AS start_date_ru,
        strftime('%d.%m.%Y', trips.end_date) AS end_date_ru,
        CAST(julianday(trips.end_date) - julianday(trips.start_date)
             AS INTEGER) + 1 AS duration,
        trips.budget,
        COALESCE(SUM(expenses.amount), 0) AS total,
        CAST(COALESCE(SUM(expenses.amount), 0) * 100 / trips.budget
             AS INTEGER) AS used_percent,
        ABS(trips.budget - COALESCE(SUM(expenses.amount), 0)) AS budget_diff,
        CASE
            WHEN trips.budget IS NULL THEN 'none'
            WHEN COALESCE(SUM(expenses.amount), 0) > trips.budget THEN 'over'
            WHEN COALESCE(SUM(expenses.amount), 0) >= trips.budget * 0.8
                THEN 'warning'
            ELSE 'ok'
        END AS budget_level
    FROM trips
    LEFT JOIN expenses
        ON expenses.trip_id = trips.id
    WHERE trips.id = ?
    GROUP BY trips.id;
"""

# Запрос 2: участники поездки.
PARTICIPANTS_QUERY = """
    SELECT
        id,
        name
    FROM participants
    WHERE trip_id = ?
    ORDER BY name;
"""

# Запрос 7: расходы поездки и кто за них платил.
TRIP_EXPENSES_QUERY = """
    SELECT
        expenses.id,
        expenses.title,
        expenses.amount,
        expenses.category,
        expenses.expense_date,
        strftime('%d.%m.%Y', expenses.expense_date) AS expense_date_ru,
        expenses.payer_id,
        participants.name AS payer_name
    FROM expenses
    JOIN participants
        ON expenses.payer_id = participants.id
    WHERE expenses.trip_id = ?
    ORDER BY expenses.expense_date, expenses.id;
"""

# Запрос 6: участники, которые пока ни за что не платили.
NOT_PAID_QUERY = """
    SELECT
        id,
        name
    FROM participants
    WHERE trip_id = ?
        AND id NOT IN (
            SELECT payer_id
            FROM expenses
            WHERE trip_id = ?
        )
    ORDER BY name;
"""

# Запрос 10: доли по всем расходам поездки.
TRIP_SHARES_QUERY = """
    SELECT
        expense_shares.expense_id,
        expense_shares.participant_id
    FROM expense_shares
    JOIN expenses
        ON expense_shares.expense_id = expenses.id
    WHERE expenses.trip_id = ?
    ORDER BY expense_shares.expense_id, expense_shares.participant_id;
"""

TRIP_RECORD_QUERY = """
    SELECT
        id,
        name,
        start_date,
        end_date,
        budget
    FROM trips
    WHERE id = ?;
"""


def trips(request):
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    try:
        trips_data = conn.execute(TRIPS_QUERY).fetchall()
    finally:
        conn.close()
    return render(request, "trips/trip_list.html", {"trips": trips_data})


def trip_detail(request, trip_id):
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    try:
        trip = conn.execute(TRIP_QUERY, [trip_id]).fetchone()
        context = {"trip": trip}
        if trip is not None:
            context.update({
                "participants": conn.execute(
                    PARTICIPANTS_QUERY, [trip_id]
                ).fetchall(),
                "expenses": conn.execute(
                    TRIP_EXPENSES_QUERY, [trip_id]
                ).fetchall(),
                "not_paid": conn.execute(
                    NOT_PAID_QUERY, [trip_id, trip_id]
                ).fetchall(),
            })
    finally:
        conn.close()
    return render(
        request,
        "trips/trip_detail.html",
        context,
        status=404 if trip is None else 200,
    )


def load_settlement(conn, trip_id):
    """Собирает объект Settlement из данных поездки в SQLite.

    Строки таблиц превращаются в объекты Trip, Participant
    и Expense, а балансы и переводы считает готовый класс Settlement.
    """
    row = conn.execute(TRIP_RECORD_QUERY, [trip_id]).fetchone()
    if row is None:
        return None
    trip = Trip(
        row["id"],
        row["name"],
        date.fromisoformat(row["start_date"]),
        date.fromisoformat(row["end_date"]),
        row["budget"] or 0,
    )
    participants = {
        item["id"]: Participant(item["id"], item["name"], trip)
        for item in conn.execute(PARTICIPANTS_QUERY, [trip_id])
    }
    shares = {}
    for item in conn.execute(TRIP_SHARES_QUERY, [trip_id]):
        shares.setdefault(item["expense_id"], []).append(
            participants[item["participant_id"]]
        )
    expenses = [
        Expense(
            item["id"],
            trip,
            item["title"],
            item["amount"],
            participants[item["payer_id"]],
            shares[item["id"]],
            item["category"],
            date.fromisoformat(item["expense_date"]),
        )
        for item in conn.execute(TRIP_EXPENSES_QUERY, [trip_id])
    ]
    return Settlement(trip, list(participants.values()), expenses)


def trip_settlement(request, trip_id):
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    try:
        settlement = load_settlement(conn, trip_id)
    finally:
        conn.close()
    context = {
        "trip": settlement.trip if settlement else None,
    }
    if settlement is not None:
        context["balances"] = [
            {
                "participant": person,
                "balance": balance,
                "status": get_settlement_status(person.name, balance),
            }
            for person, balance in settlement.get_balances().items()
        ]
        context["transfers"] = settlement.get_transfers()
    return render(
        request,
        "trips/trip_settlement.html",
        context,
        status=404 if settlement is None else 200,
    )
