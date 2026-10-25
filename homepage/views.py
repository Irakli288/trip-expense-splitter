import sqlite3

from django.shortcuts import render

from db.database import get_connection

# Запрос 11 из sql/queries.sql: сводка сервиса.
SUMMARY_QUERY = """
    SELECT
        (SELECT COUNT(*) FROM trips) AS trips_count,
        (SELECT COUNT(*) FROM participants) AS participants_count,
        COUNT(*) AS expenses_count,
        COALESCE(SUM(amount), 0) AS expenses_total,
        MAX(amount) AS max_amount
    FROM expenses;
"""


def index(request):
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    try:
        summary = conn.execute(SUMMARY_QUERY).fetchone()
    finally:
        conn.close()
    return render(request, "homepage/index.html", {"summary": summary})
