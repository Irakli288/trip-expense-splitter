"""Функции для работы с участниками поездок."""


def add_participant(
    participants: list[dict],
    trip_id: int,
    name: str
) -> dict:
    """Добавить участника в поездку и вернуть его данные.

    Имена участников внутри одной поездки не повторяются:
    при повторе выбрасывается ValueError.
    """
    names = {item["name"].lower()
             for item in get_trip_participants(participants, trip_id)}
    if name.lower() in names:
        raise ValueError(f"Участник «{name}» уже есть в поездке")
    participant_id = max((item["id"] for item in participants), default=0) + 1
    participant = {"id": participant_id, "trip_id": trip_id, "name": name}
    participants.append(participant)
    return participant


def get_trip_participants(
    participants: list[dict],
    trip_id: int
) -> list[dict]:
    """Вернуть участников указанной поездки."""
    return [item for item in participants if item["trip_id"] == trip_id]


def get_names(participants: list[dict]) -> dict[int, str]:
    """Вернуть словарь «идентификатор участника → имя»."""
    return {item["id"]: item["name"] for item in participants}
