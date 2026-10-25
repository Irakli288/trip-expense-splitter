"""Класс Trip и функции для работы с коллекцией поездок."""

from datetime import date

from utils import format_money


class Trip:
    """Совместная поездка: название, даты и бюджет."""

    def __init__(
        self,
        trip_id: int,
        name: str,
        start_date: date,
        end_date: date,
        budget: float,
    ) -> None:
        """Создать поездку; даты проверяются при создании объекта."""
        if not Trip.validate_dates(start_date, end_date):
            raise ValueError("Дата окончания раньше даты начала")
        self.id = trip_id
        self.name = name
        self.start_date = start_date
        self.end_date = end_date
        self.budget = budget

    @staticmethod
    def validate_dates(start_date: date, end_date: date) -> bool:
        """Проверить, что поездка не заканчивается раньше, чем начинается."""
        return start_date <= end_date

    @property
    def duration(self) -> int:
        """Длительность поездки в днях, включая оба дня (из ПР1)."""
        return (self.end_date - self.start_date).days + 1

    def check_budget(self, total_amount: float) -> str:
        """Сравнить сумму расходов с бюджетом поездки (из ПР1)."""
        if self.budget <= 0:
            return "Бюджет не задан"
        used_percent = int(total_amount / self.budget * 100)
        if total_amount > self.budget:
            overrun = format_money(total_amount - self.budget)
            return f"Бюджет превышен на {overrun}"
        elif used_percent >= 80:
            return f"Внимание: израсходовано {used_percent}% бюджета"
        else:
            return f"Расходы в пределах бюджета ({used_percent}%)"

    def budget_level(self, total_amount: float) -> str:
        """Вернуть уровень расходования бюджета (добавлен в ПР6).

        none — бюджет не задан, ok — в пределах бюджета,
        warning — израсходовано 80% и больше, over — бюджет превышен.
        Шаблоны выбирают по уровню цвет отметки бюджета.
        """
        if self.budget <= 0:
            return "none"
        if total_amount > self.budget:
            return "over"
        if total_amount >= self.budget * 0.8:
            return "warning"
        return "ok"

    def __str__(self) -> str:
        """Вернуть строку вида «Название: даты (дни), бюджет»."""
        return (f"{self.name}: {self.start_date:%d.%m.%Y} – "
                f"{self.end_date:%d.%m.%Y} ({self.duration} дн.), "
                f"бюджет {format_money(self.budget)}")


def add_trip(
    trips: list[Trip],
    name: str,
    start_date: date,
    end_date: date,
    budget: float,
) -> Trip:
    """Создать объект Trip, добавить его в коллекцию и вернуть."""
    trip_id = max((trip.id for trip in trips), default=0) + 1
    trip = Trip(trip_id, name, start_date, end_date, budget)
    trips.append(trip)
    return trip


def find_trip_by_id(trips: list[Trip], trip_id: int) -> Trip | None:
    """Вернуть поездку с указанным номером или None."""
    for trip in trips:
        if trip.id == trip_id:
            return trip
    return None


def get_trip(trips: list[Trip], trip_id: int) -> Trip:
    """Вернуть поездку по номеру или выбросить KeyError."""
    trip = find_trip_by_id(trips, trip_id)
    if trip is None:
        raise KeyError(f"Поездка № {trip_id} не найдена")
    return trip


def find_trips(trips: list[Trip], query: str) -> list[Trip]:
    """Найти поездки, в названии которых есть подстрока query."""
    query = query.lower()
    return [trip for trip in trips if query in trip.name.lower()]


def sort_trips(trips: list[Trip]) -> list[Trip]:
    """Вернуть поездки, упорядоченные по дате начала."""
    return sorted(trips, key=lambda trip: trip.start_date)


def show_trips(trips: list[Trip]) -> None:
    """Вывести список поездок, упорядоченный по дате начала."""
    if not trips:
        print("Поездок пока нет")
        return
    for trip in sort_trips(trips):
        print(f"{trip.id:>3}. {trip}")
