from datetime import date

import pytest

from models import Participant, Trip


@pytest.fixture
def trip():
    return Trip(1, "Поездка в Казань", date(2026, 11, 3),
                date(2026, 11, 6), 60000)


@pytest.fixture
def people(trip):
    return [
        Participant(1, "Ираклий", trip),
        Participant(2, "Анна", trip),
        Participant(3, "Максим", trip),
    ]
