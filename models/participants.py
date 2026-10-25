"""Класс Participant и функции для работы с участниками поездок."""

from .trips import Trip


class Participant:
    """Участник поездки."""

    def __init__(self, participant_id: int, name: str, trip: Trip) -> None:
        """Создать участника, связанного с объектом поездки."""
        self.id = participant_id
        self.name = name
        self.trip = trip

    @classmethod
    def from_data(cls, data: dict, trip: Trip) -> "Participant":
        """Создать участника из записи JSON и найденной поездки."""
        return cls(data["id"], data["name"], trip)

    def __str__(self) -> str:
        """Вернуть строку вида «Имя (поездка)»."""
        return f"{self.name} ({self.trip.name})"


def get_trip_participants(
    participants: list[Participant],
    trip: Trip,
) -> list[Participant]:
    """Вернуть участников указанной поездки."""
    return [item for item in participants if item.trip is trip]


def add_participant(
    participants: list[Participant],
    trip: Trip,
    name: str,
) -> Participant:
    """Создать участника поездки, добавить в коллекцию и вернуть.

    Имена участников внутри одной поездки не повторяются:
    при повторе выбрасывается ValueError.
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
    """Вернуть участника с указанным номером или None."""
    for participant in participants:
        if participant.id == participant_id:
            return participant
    return None


def find_participant(
    participants: list[Participant],
    query: str,
) -> list[Participant]:
    """Найти участников, в имени которых есть подстрока query."""
    query = query.lower()
    return [item for item in participants if query in item.name.lower()]


def show_participants(participants: list[Participant]) -> None:
    """Вывести участников поездки."""
    if not participants:
        print("В поездке нет участников")
        return
    for participant in participants:
        print(f"{participant.id:>3}. {participant.name}")
