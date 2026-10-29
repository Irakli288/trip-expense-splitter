"""Класс Participant и функции для работы с участниками поездок."""

from .trips import Trip


class Participant:
    """Участник поездки."""

    def __init__(self, participant_id: int, name: str, trip: Trip) -> None:
        """Создает участника и привязывает его к поездке."""
        self.id = participant_id
        self.name = name
        self.trip = trip

    @classmethod
    def from_data(cls, data: dict, trip: Trip) -> "Participant":
        """Создает участника из записи JSON и уже найденной поездки."""
        return cls(data["id"], data["name"], trip)

    def __str__(self) -> str:
        """Возвращает строку вида «Имя (поездка)»."""
        return f"{self.name} ({self.trip.name})"


def get_trip_participants(
    participants: list[Participant],
    trip: Trip,
) -> list[Participant]:
    """Возвращает участников нужной поездки."""
    return [item for item in participants if item.trip is trip]


def add_participant(
    participants: list[Participant],
    trip: Trip,
    name: str,
) -> Participant:
    """Создает участника поездки, добавляет в список и возвращает.

    В одной поездке не может быть двух участников с одинаковым
    именем, в таком случае будет ValueError.
    """
    names = {item.name.lower()
             for item in get_trip_participants(participants, trip)}
    if name.lower() in names:
        raise ValueError(f"Участник «{name}» уже есть в поездке")
    participant_id = max((item.id for item in participants), default=0) + 1
    participant = Participant(participant_id, name, trip)
    participants.append(participant)
    return participant


def find_participant_by_id(
    participants: list[Participant],
    participant_id: int,
) -> Participant | None:
    """Возвращает участника с таким номером или None, если его нет."""
    for participant in participants:
        if participant.id == participant_id:
            return participant
    return None


def find_participant(
    participants: list[Participant],
    query: str,
) -> list[Participant]:
    """Ищет участников, у которых в имени есть строка query."""
    query = query.lower()
    return [item for item in participants if query in item.name.lower()]


def show_participants(participants: list[Participant]) -> None:
    """Печатает участников поездки."""
    if not participants:
        print("В поездке нет участников")
        return
    for participant in participants:
        print(f"{participant.id:>3}. {participant.name}")
