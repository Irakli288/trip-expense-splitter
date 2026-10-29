"""Тесты работы с базой SQLite."""

import sqlite3
from pathlib import Path

import pytest

from db import import_json
from db.database import BASE_DIR, get_connection

QUERIES_FILE = BASE_DIR / "sql" / "queries.sql"


@pytest.fixture
def conn(tmp_path: Path):
    db_path = tmp_path / "test.sqlite"
    import_json.main(db_path)
    connection = get_connection(db_path)
    yield connection
    connection.close()


def test_tables_created(conn):
    tables = {row[0] for row in conn.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table'"
    )}
    assert tables == {"trips", "participants", "expenses", "expense_shares"}


def test_foreign_keys_declared(conn):
    targets = {row[2] for row in conn.execute(
        "PRAGMA foreign_key_list(expenses)"
    )}
    assert targets == {"trips", "participants"}


def test_json_data_imported(conn):
    counts = [
        conn.execute("SELECT COUNT(*) FROM trips").fetchone()[0],
        conn.execute("SELECT COUNT(*) FROM participants").fetchone()[0],
        conn.execute("SELECT COUNT(*) FROM expenses").fetchone()[0],
        conn.execute("SELECT COUNT(*) FROM expense_shares").fetchone()[0],
    ]
    assert counts == [2, 5, 6, 15]


def test_import_can_be_repeated(tmp_path: Path):
    db_path = tmp_path / "test.sqlite"
    import_json.main(db_path)
    import_json.main(db_path)
    connection = sqlite3.connect(db_path)
    count = connection.execute("SELECT COUNT(*) FROM trips").fetchone()
    connection.close()
    assert count == (2,)


def test_foreign_key_is_checked(conn):
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            "INSERT INTO participants (id, trip_id, name) VALUES (?, ?, ?)",
            (100, 999, "Призрак"),
        )


def test_amount_must_be_positive(conn):
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            "INSERT INTO expenses (trip_id, title, amount, expense_date,"
            " payer_id) VALUES (?, ?, ?, ?, ?)",
            (1, "Ошибка", -10, "2026-11-03", 1),
        )


def test_all_saved_queries_run(conn):
    lines = QUERIES_FILE.read_text(encoding="utf-8").splitlines()
    script = "\n".join(
        line for line in lines if not line.lstrip().startswith("--")
    )
    queries = [part for part in script.split(";") if "SELECT" in part]
    assert len(queries) >= 10
    for query in queries:
        conn.execute(query).fetchall()


def test_parameterized_query(conn):
    rows = conn.execute(
        "SELECT title FROM expenses WHERE category = ? ORDER BY id",
        ("транспорт",),
    ).fetchall()
    assert rows == [("Билеты на поезд",), ("Трансфер до турбазы",)]
