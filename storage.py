"""Сохранение и загрузка объектов проекта в JSON-файлах.

JSON остается форматом хранения: при загрузке записи превращаются
в объекты Trip, Participant и Expense, а при сохранении объекты
превращаются обратно в записи. Связи между объектами хранятся
в файлах как номера: trip_id, payer_id, split_between.
"""

import json
from datetime import date
from pathlib import Path

from models import Expense, Participant, Trip
from models.participants import find_participant_by_id
from models.trips import find_trip_by_id

DATA_DIR = Path(__file__).parent / "data"
TRIPS_FILE = DATA_DIR / "trips.json"
PARTICIPANTS_FILE = DATA_DIR / "participants.json"
EXPENSES_FILE = DATA_DIR / "expenses.json"


def load_records(filename: Path) -> list[dict]:
    """Загрузить список записей из JSON-файла.

    Если файла нет, возвращается пустой список. Если файл поврежден
    или содержит не список, выводится предупреждение и тоже
    возвращается пустой список — программа продолжает работу.
    """
    try:
        with open(filename, encoding="utf-8") as file:
            records = json.load(file)
    except FileNotFoundError:
        return []
    except json.JSONDecodeError as error:
        print(f"Предупреждение: файл {filename.name} поврежден ({error})")
        return []
    if not isinstance(records, list):
        print(f"Предупреждение: в файле {filename.name} ожидался список")
        return []
    return records


def save_records(filename: Path, records: list[dict]) -> None:
    """Сохранить список записей в JSON-файл."""
    filename.parent.mkdir(parents=True, exist_ok=True)
    with open(filename, "w", encoding="utf-8") as file:
        json.dump(records, file, ensure_ascii=False, indent=4)


def skip_record(filename: Path, data: object, reason: str) -> None:
    """Сообщить, что запись файла пропущена при загрузке."""
    print(f"Предупреждение: в файле {filename.name} пропущена запись "
          f"{data} ({reason})")


def load_trips(filename: Path = TRIPS_FILE) -> list[Trip]:
    """Загрузить поездки и вернуть коллекцию объектов Trip."""
    trips = []
    for data in load_records(filename):
        try:
            trips.append(Trip(
                trip_id=data["id"],
                name=data["name"],
                start_date=date.fromisoformat(data["start_date"]),
                end_date=date.fromisoformat(data["end_date"]),
                budget=data["budget"],
            ))
        except (KeyError, TypeError, ValueError) as error:
            skip_record(filename, data, str(error))
    return trips


def save_trips(trips: list[Trip], filename: Path = TRIPS_FILE) -> None:
    """Преобразовать объекты Trip в записи и сохранить их."""
    save_records(filename, [
        {
            "id": trip.id,
            "name": trip.name,
            "start_date": trip.start_date.isoformat(),
            "end_date": trip.end_date.isoformat(),
            "budget": trip.budget,
        }
        for trip in trips
    ])


def load_participants(
    trips: list[Trip],
    filename: Path = PARTICIPANTS_FILE,
) -> list[Participant]:
    """Загрузить участников и связать каждого с объектом Trip."""
    participants = []
    for data in load_records(filename):
        try:
            trip = find_trip_by_id(trips, data["trip_id"])
            if trip is None:
                raise ValueError(f"нет поездки № {data['trip_id']}")
            participants.append(Participant.from_data(data, trip))
        except (KeyError, TypeError, ValueError) as error:
            skip_record(filename, data, str(error))
    return participants


def save_participants(
    participants: list[Participant],
    filename: Path = PARTICIPANTS_FILE,
) -> None:
    """Сохранить участников; поездка записывается номером trip_id."""
    save_records(filename, [
        {"id": item.id, "trip_id": item.trip.id, "name": item.name}
        for item in participants
    ])


def load_expenses(
    trips: list[Trip],
    participants: list[Participant],
    filename: Path = EXPENSES_FILE,
) -> list[Expense]:
    """Загрузить расходы и восстановить ссылки на поездку и участников.

    Расход, ссылающийся на несуществующую поездку или участника,
    не создается: выводится предупреждение и запись пропускается.
    """
    expenses = []
    for data in load_records(filename):
        try:
            trip = find_trip_by_id(trips, data["trip_id"])
            if trip is None:
                raise ValueError(f"нет поездки № {data['trip_id']}")
            people = []
            for participant_id in [data["payer_id"], *data["split_between"]]:
                participant = find_participant_by_id(participants,
                                                     participant_id)
                if participant is None:
                    raise ValueError(f"нет участника № {participant_id}")
                people.append(participant)
            expenses.append(Expense(
                expense_id=data["id"],
                trip=trip,
                title=data["title"],
                amount=data["amount"],
                payer=people[0],
                split_between=people[1:],
                category=data["category"],
                expense_date=date.fromisoformat(data["date"]),
            ))
        except (KeyError, TypeError, ValueError) as error:
            skip_record(filename, data, str(error))
    return expenses


def save_expenses(
    expenses: list[Expense],
    filename: Path = EXPENSES_FILE,
) -> None:
    """Сохранить расходы; связанные объекты записываются номерами."""
    save_records(filename, [
        {
            "id": item.id,
            "trip_id": item.trip.id,
            "title": item.title,
            "amount": item.amount,
            "category": item.category,
            "date": item.date.isoformat(),
            "payer_id": item.payer.id,
            "split_between": [person.id for person in item.split_between],
        }
        for item in expenses
    ])
