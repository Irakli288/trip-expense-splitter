from datetime import date

import pytest

from trips import add_trip, check_budget, find_trips, get_trip_duration


def test_trip_duration():
    assert get_trip_duration(date(2026, 11, 3), date(2026, 11, 6)) == 4


def test_add_trip():
    trips = {}
    add_trip(trips, "Поездка в Казань", date(2026, 11, 3),
             date(2026, 11, 6), 60000)
    assert trips[1]["start_date"] == "2026-11-03"


def test_add_trip_wrong_dates():
    with pytest.raises(ValueError):
        add_trip({}, "Поездка", date(2026, 11, 6), date(2026, 11, 3), 1000)


def test_find_trips():
    trips = {}
    add_trip(trips, "Поездка в Казань", date(2026, 11, 3),
             date(2026, 11, 6), 60000)
    assert find_trips(trips, "казань")


def test_check_budget():
    assert "превышен" in check_budget(31000, 30000)
    assert "Внимание" in check_budget(25500, 30000)
