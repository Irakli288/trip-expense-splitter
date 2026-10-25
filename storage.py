"""Сохранение и загрузка данных проекта в JSON-файлах."""

import json
from pathlib import Path

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


def load_trips() -> dict[int, dict]:
    """Загрузить поездки в словарь «идентификатор → данные поездки»."""
    return {trip["id"]: trip for trip in load_records(TRIPS_FILE)}


def save_trips(trips: dict[int, dict]) -> None:
    """Сохранить словарь поездок в trips.json."""
    save_records(TRIPS_FILE, list(trips.values()))


def load_participants() -> list[dict]:
    """Загрузить список участников."""
    return load_records(PARTICIPANTS_FILE)


def save_participants(participants: list[dict]) -> None:
    """Сохранить список участников в participants.json."""
    save_records(PARTICIPANTS_FILE, participants)


def load_expenses() -> list[dict]:
    """Загрузить список расходов."""
    return load_records(EXPENSES_FILE)


def save_expenses(expenses: list[dict]) -> None:
    """Сохранить список расходов в expenses.json."""
    save_records(EXPENSES_FILE, expenses)
