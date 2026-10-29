"""Класс Trip и функции для работы со списком поездок."""

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
        """Создает поездку. Даты проверяются сразу при создании."""
        if not Trip.validate_dates(start_date, end_date):
            raise ValueError("Дата окончания раньше даты начала")
        self.id = trip_id
        self.name = name
        self.start_date = start_date
        self.end_date = end_date
        self.budget = budget

    @staticmethod
    def validate_dates(start_date: date, end_date: date) -> bool:
        """Проверяет, что поездка не заканчивается раньше, чем начинается."""
        return start_date <= end_date

    @property
    def duration(self) -> int:
        """Сколько дней длится поездка, считая первый и последний день."""
        return (self.end_date - self.start_date).days + 1

    def check_budget(self, total_amount: float) -> str:
        """Сравнивает потраченное с бюджетом поездки."""
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
        """Насколько потрачен бюджет.

        none — бюджета нет, ok — укладываемся, warning — потрачено
        80% и больше, over — бюджет превышен. По этому значению
        шаблоны выбирают цвет отметки бюджета.
        """
        if self.budget <= 0:
            return "none"
        if total_amount > self.budget:
            return "over"
        if total_amount >= self.budget * 0.8:
            return "warning"
        return "ok"

    def __str__(self) -> str:
        """Возвращает строку вида «Название: даты (дни), бюджет»."""
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
    """Создает поездку, добавляет ее в список и возвращает."""
    trip_id = max((trip.id for trip in trips), default=0) + 1
    trip = Trip(trip_id, name, start_date, end_date, budget)
    trips.append(trip)
    return trip


def find_trip_by_id(trips: list[Trip], trip_id: int) -> Trip | None:
    """Возвращает поездку с таким номером или None, если ее нет."""
    for trip in trips:
        if trip.id == trip_id:
            return trip
    return None


def get_trip(trips: list[Trip], trip_id: int) -> Trip:
    """Возвращает поездку по номеру, если нет такой, то KeyError."""
    trip = find_trip_by_id(trips, trip_id)
    if trip is None:
        raise KeyError(f"Поездка № {trip_id} не найдена")
    return trip


def find_trips(trips: list[Trip], query: str) -> list[Trip]:
    """Ищет поездки, у которых в названии есть строка query."""
    query = query.lower()
    return [trip for trip in trips if query in trip.name.lower()]


def sort_trips(trips: list[Trip]) -> list[Trip]:
    """Возвращает поездки по порядку дат начала."""
    return sorted(trips, key=lambda trip: trip.start_date)


def show_trips(trips: list[Trip]) -> None:
    """Печатает список поездок по порядку дат начала."""
    if not trips:
        print("Поездок пока нет")
        return
    for trip in sort_trips(trips):
        print(f"{trip.id:>3}. {trip}")
