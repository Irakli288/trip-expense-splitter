from datetime import date

import pytest

from models import Trip
from models.trips import add_trip, find_trips, get_trip, sort_trips


def test_trip_creation(trip):
    assert trip.id == 1
    assert trip.name == "Поездка в Казань"
    assert trip.start_date == date(2026, 11, 3)
    assert trip.budget == 60000


def test_trip_duration(trip):
    assert trip.duration == 4


def test_trip_str(trip):
    assert str(trip) == ("Поездка в Казань: 03.11.2026 – 06.11.2026 "
                         "(4 дн.), бюджет 60000.00 ₽")


def test_trip_wrong_dates():
    assert not Trip.validate_dates(date(2026, 11, 6), date(2026, 11, 3))
    with pytest.raises(ValueError):
        Trip(1, "Поездка", date(2026, 11, 6), date(2026, 11, 3), 1000)


def test_check_budget():
    trip = Trip(1, "Поездка", date(2026, 11, 3), date(2026, 11, 6), 30000)
    assert "превышен" in trip.check_budget(31000)
    assert "Внимание" in trip.check_budget(25500)
    assert "в пределах" in trip.check_budget(1000)


def test_add_and_get_trip():
    trips = []
    trip = add_trip(trips, "Поездка в Казань", date(2026, 11, 3),
                    date(2026, 11, 6), 60000)
    assert isinstance(trip, Trip)
    assert trips == [trip]
    assert get_trip(trips, 1) is trip
    with pytest.raises(KeyError):
        get_trip(trips, 5)


def test_find_and_sort_trips():
    trips = []
    add_trip(trips, "Поход на Алтай", date(2027, 7, 10),
             date(2027, 7, 20), 90000)
    add_trip(trips, "Поездка в Казань", date(2026, 11, 3),
             date(2026, 11, 6), 60000)
    assert [trip.name for trip in find_trips(trips, "казань")] == [
        "Поездка в Казань"
    ]
    assert sort_trips(trips)[0].name == "Поездка в Казань"
