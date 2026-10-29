import sqlite3

from django.shortcuts import render

from db.database import get_connection
from models.expenses import CATEGORIES, calculate_share

# Запрос 1 из sql/queries.sql: поездки для списка в форме поиска.
TRIPS_QUERY = """
    SELECT
        id,
        name
    FROM trips
    ORDER BY start_date;
"""

# Запрос 4: ищем расходы по поездке, категории и минимальной сумме.
# Часть (? = 0 OR ...) выключает фильтр, если поездка не выбрана,
# а (? = '' OR ...) делает то же, если не выбрана категория.
EXPENSES_QUERY = """
    SELECT
        expenses.id,
        strftime('%d.%m.%Y', expenses.expense_date) AS expense_date_ru,
        expenses.title,
        expenses.category,
        expenses.amount,
        trips.id AS trip_id,
        trips.name AS trip_name,
        participants.name AS payer_name
    FROM expenses
    JOIN trips
        ON expenses.trip_id = trips.id
    JOIN participants
        ON expenses.payer_id = participants.id
    WHERE (? = 0 OR expenses.trip_id = ?)
        AND (? = '' OR expenses.category = ?)
        AND expenses.amount >= ?
    ORDER BY expenses.expense_date, expenses.id;
"""

# Запрос 5: сколько расходов нашлось и на какую сумму.
EXPENSES_TOTAL_QUERY = """
    SELECT
        COUNT(*) AS expenses_count,
        COALESCE(SUM(amount), 0) AS expenses_total
    FROM expenses
    WHERE (? = 0 OR trip_id = ?)
        AND (? = '' OR category = ?)
        AND amount >= ?;
"""

# Запрос 8: расход по номеру вместе с поездкой и плательщиком.
EXPENSE_QUERY = """
    SELECT
        expenses.id,
        expenses.title,
        expenses.amount,
        expenses.category,
        strftime('%d.%m.%Y', expenses.expense_date) AS expense_date_ru,
        trips.id AS trip_id,
        trips.name AS trip_name,
        participants.name AS payer_name
    FROM expenses
    JOIN trips
        ON expenses.trip_id = trips.id
    JOIN participants
        ON expenses.payer_id = participants.id
    WHERE expenses.id = ?;
"""

# Запрос 9: на кого делится расход.
SHARES_QUERY = """
    SELECT
        participants.id,
        participants.name
    FROM expense_shares
    JOIN participants
        ON expense_shares.participant_id = participants.id
    WHERE expense_shares.expense_id = ?
    ORDER BY participants.id;
"""

# Запрос 14: сколько потрачено по каждой категории.
CATEGORY_TOTALS_QUERY = """
    SELECT
        category,
        COUNT(*) AS expenses_count,
        SUM(amount) AS total,
        ROUND(AVG(amount), 2) AS average_amount,
        MAX(amount) AS max_amount
    FROM expenses
    GROUP BY category
    ORDER BY total DESC;
"""

# Запрос 15: сколько заплатил каждый участник.
PAYERS_QUERY = """
    SELECT
        participants.name AS participant_name,
        trips.name AS trip_name,
        COUNT(expenses.id) AS expenses_count,
        COALESCE(SUM(expenses.amount), 0) AS paid_total
    FROM participants
    JOIN trips
        ON participants.trip_id = trips.id
    LEFT JOIN expenses
        ON expenses.payer_id = participants.id
    GROUP BY participants.id
    ORDER BY paid_total DESC, participants.name;
"""

# Запрос 16: категории, где потрачено не меньше заданной суммы.
BIG_CATEGORIES_QUERY = """
    SELECT
        category,
        SUM(amount) AS total
    FROM expenses
    GROUP BY category
    HAVING SUM(amount) >= ?
    ORDER BY total DESC;
"""

# Запрос 17: поездки, где потрачено 80% бюджета и больше.
BUDGET_ALERTS_QUERY = """
    SELECT
        trips.id,
        trips.name,
        trips.budget,
        SUM(expenses.amount) AS total,
        CAST(SUM(expenses.amount) * 100 / trips.budget AS INTEGER)
            AS used_percent
    FROM trips
    JOIN expenses
        ON expenses.trip_id = trips.id
    WHERE trips.budget IS NOT NULL
    GROUP BY trips.id
    HAVING SUM(expenses.amount) >= trips.budget * 0.8
    ORDER BY used_percent DESC;
"""

# Запрос 3: три самых дорогих расхода.
TOP_EXPENSES_QUERY = """
    SELECT
        expenses.id,
        expenses.title,
        expenses.amount,
        trips.name AS trip_name
    FROM expenses
    JOIN trips
        ON expenses.trip_id = trips.id
    ORDER BY expenses.amount DESC
    LIMIT 3;
"""

DEFAULT_MIN_TOTAL = 5000


def parse_number(text, default=0, number_type=float):
    """Превращает параметр из адреса в неотрицательное число.

    Если значение пустое или кривое, берется значение по умолчанию.
    Так опечатка в адресе не ломает страницу.
    """
    try:
        value = number_type(text)
    except (TypeError, ValueError):
        return default
    return value if value >= 0 else default


def expenses(request):
    trip_id = parse_number(request.GET.get("trip"), 0, int)
    category = request.GET.get("category", "")
    if category not in CATEGORIES:
        category = ""
    min_amount = parse_number(request.GET.get("min_amount"), 0)
    params = [trip_id, trip_id, category, category, min_amount]

    conn = get_connection()
    conn.row_factory = sqlite3.Row
    try:
        expenses_data = conn.execute(EXPENSES_QUERY, params).fetchall()
        summary = conn.execute(EXPENSES_TOTAL_QUERY, params).fetchone()
        trips_data = conn.execute(TRIPS_QUERY).fetchall()
    finally:
        conn.close()
    context = {
        "expenses": expenses_data,
        "summary": summary,
        "trips": trips_data,
        "categories": CATEGORIES,
        "selected_trip": trip_id,
        "selected_category": category,
        "min_amount": request.GET.get("min_amount", ""),
    }
    return render(request, "expenses/expense_list.html", context)


def expense_detail(request, expense_id):
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    try:
        expense = conn.execute(EXPENSE_QUERY, [expense_id]).fetchone()
        shares = []
        if expense is not None:
            shares = conn.execute(SHARES_QUERY, [expense_id]).fetchall()
    finally:
        conn.close()
    context = {
        "expense": expense,
        "shares": shares,
        "share": (calculate_share(expense["amount"], len(shares))
                  if shares else 0),
    }
    return render(
        request,
        "expenses/expense_detail.html",
        context,
        status=404 if expense is None else 200,
    )


def statistics(request):
    min_total = parse_number(request.GET.get("min_total"), DEFAULT_MIN_TOTAL)
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    try:
        context = {
            "categories": conn.execute(CATEGORY_TOTALS_QUERY).fetchall(),
            "payers": conn.execute(PAYERS_QUERY).fetchall(),
            "big_categories": conn.execute(
                BIG_CATEGORIES_QUERY, [min_total]
            ).fetchall(),
            "budget_alerts": conn.execute(BUDGET_ALERTS_QUERY).fetchall(),
            "top_expenses": conn.execute(TOP_EXPENSES_QUERY).fetchall(),
            "min_total": request.GET.get("min_total", DEFAULT_MIN_TOTAL),
        }
    finally:
        conn.close()
    return render(request, "expenses/statistics.html", context)
