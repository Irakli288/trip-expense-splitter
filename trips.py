"""Функции для работы с поездками."""

from datetime import date

from utils import format_money


def get_trip_duration(start_date: date, end_date: date) -> int:
    """Вернуть длительность поездки в днях (включая оба дня).

    Функция из ПР1. Если дата окончания раньше даты начала,
    возвращает 0.
    """
    if end_date < start_date:
        return 0
    return (end_date - start_date).days + 1


def add_trip(
    trips: dict[int, dict],
    name: str,
    start_date: date,
    end_date: date,
    budget: float
) -> dict:
    """Добавить поездку в словарь trips и вернуть ее данные.

    Даты хранятся строками ISO (ГГГГ-ММ-ДД), чтобы их можно
    было без преобразований записать в JSON.
    """
    if get_trip_duration(start_date, end_date) == 0:
        raise ValueError("Дата окончания раньше даты начала")
    trip_id = max(trips, default=0) + 1
    trip = {
        "id": trip_id,
        "name": name,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "budget": budget,
    }
    trips[trip_id] = trip
    return trip


def get_trip(trips: dict[int, dict], trip_id: int) -> dict:
    """Вернуть поездку по номеру или выбросить KeyError."""
    if trip_id not in trips:
        raise KeyError(f"Поездка № {trip_id} не найдена")
    return trips[trip_id]


def find_trips(trips: dict[int, dict], query: str) -> list[dict]:
    """Найти поездки, в названии которых есть подстрока query."""
    query = query.lower()
    return [trip for trip in trips.values() if query in trip["name"].lower()]


def sort_trips(trips: dict[int, dict]) -> list[dict]:
    """Вернуть поездки, упорядоченные по дате начала."""
    return sorted(trips.values(), key=lambda trip: trip["start_date"])


def check_budget(total_amount: float, budget: float) -> str:
    """Сравнить сумму расходов с бюджетом поездки (функция из ПР1)."""
    if budget <= 0:
        return "Бюджет не задан"
    used_percent = int(total_amount / budget * 100)
    if total_amount > budget:
        return f"Бюджет превышен на {format_money(total_amount - budget)}"
    elif used_percent >= 80:
        return f"Внимание: израсходовано {used_percent}% бюджета"
    else:
        return f"Расходы в пределах бюджета ({used_percent}%)"
