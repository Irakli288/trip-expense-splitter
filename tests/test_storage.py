from datetime import date

from models import Expense
from storage import (
    load_expenses,
    load_participants,
    load_records,
    load_trips,
    save_expenses,
    save_participants,
    save_records,
    save_trips,
)


def test_save_and_load_records(tmp_path):
    filename = tmp_path / "expenses.json"
    save_records(filename, [{"id": 1, "title": "Ужин"}])
    assert load_records(filename) == [{"id": 1, "title": "Ужин"}]


def test_load_missing_file(tmp_path):
    assert load_records(tmp_path / "nope.json") == []


def test_load_broken_file(tmp_path):
    filename = tmp_path / "broken.json"
    filename.write_text("{не json", encoding="utf-8")
    assert load_records(filename) == []


def test_objects_round_trip(tmp_path, trip, people):
    expense = Expense(1, trip, "Экскурсия", 3000, people[1], people[1:],
                      "развлечения", date(2026, 11, 5))
    save_trips([trip], tmp_path / "trips.json")
    save_participants(people, tmp_path / "participants.json")
    save_expenses([expense], tmp_path / "expenses.json")
    assert load_records(tmp_path / "expenses.json")[0]["split_between"] == [
        2, 3
    ]

    trips = load_trips(tmp_path / "trips.json")
    participants = load_participants(trips, tmp_path / "participants.json")
    expenses = load_expenses(trips, participants,
                             tmp_path / "expenses.json")
    assert trips[0].start_date == date(2026, 11, 3)
    assert participants[0].trip is trips[0]
    loaded = expenses[0]
    assert loaded.trip is trips[0]
    assert loaded.payer is participants[1]
    assert loaded.split_between == participants[1:]


def test_skip_expense_with_unknown_participant(tmp_path, trip, people):
    save_records(tmp_path / "expenses.json", [
        {"id": 1, "trip_id": 1, "title": "Ужин", "amount": 900.0,
         "category": "еда", "date": "2026-11-04", "payer_id": 7,
         "split_between": [1, 2]}
    ])
    assert load_expenses([trip], people, tmp_path / "expenses.json") == []
