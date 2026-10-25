import pytest

from models import Participant
from models.participants import (
    add_participant,
    find_participant,
    find_participant_by_id,
    get_trip_participants,
)


def test_participant_creation(trip):
    participant = Participant(1, "Ираклий", trip)
    assert participant.id == 1
    assert participant.name == "Ираклий"
    assert participant.trip is trip
    assert str(participant) == "Ираклий (Поездка в Казань)"


def test_participant_from_data(trip):
    participant = Participant.from_data(
        {"id": 2, "trip_id": 1, "name": "Анна"}, trip
    )
    assert participant.id == 2
    assert participant.name == "Анна"
    assert participant.trip is trip


def test_add_participant(trip):
    participants = []
    participant = add_participant(participants, trip, "Ираклий")
    assert participants == [participant]
    assert participant.id == 1
    with pytest.raises(ValueError):
        add_participant(participants, trip, "ираклий")


def test_find_participants(trip, people):
    assert find_participant_by_id(people, 2).name == "Анна"
    assert find_participant_by_id(people, 9) is None
    assert find_participant(people, "макс") == [people[2]]
    assert get_trip_participants(people, trip) == people
