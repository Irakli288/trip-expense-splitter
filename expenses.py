"""Функции для работы с расходами поездки."""

from collections.abc import Iterator
from datetime import date

CATEGORIES = ("жилье", "транспорт", "еда", "развлечения", "прочее")


def add_expense(
    expenses: list[dict],
    trip_id: int,
    title: str,
    amount: float,
    payer_id: int,
    split_between: list[int],
    category: str = "прочее",
    expense_date: date | None = None
) -> dict:
    """Добавить расход в список expenses и вернуть его данные.

    split_between — идентификаторы участников, между которыми
    делится расход; плательщик не обязан входить в этот список.
    """
    if amount <= 0:
        raise ValueError("Сумма расхода должна быть больше нуля")
    if not split_between:
        raise ValueError("Расход должен делиться хотя бы на одного участника")
    if category not in CATEGORIES:
        raise ValueError(f"Неизвестная категория: {category}")
    expense_id = max((item["id"] for item in expenses), default=0) + 1
    expense = {
        "id": expense_id,
        "trip_id": trip_id,
        "title": title,
        "amount": amount,
        "category": category,
        "date": (expense_date or date.today()).isoformat(),
        "payer_id": payer_id,
        "split_between": sorted(set(split_between)),
    }
    expenses.append(expense)
    return expense


def delete_expense(expenses: list[dict], expense_id: int) -> dict:
    """Удалить расход по идентификатору и вернуть его.

    Если расхода нет, выбрасывается KeyError.
    """
    for index, expense in enumerate(expenses):
        if expense["id"] == expense_id:
            return expenses.pop(index)
    raise KeyError(f"Расход № {expense_id} не найден")


def iter_trip_expenses(expenses: list[dict], trip_id: int) -> Iterator[dict]:
    """Генератор: по одному выдает расходы указанной поездки."""
    for expense in expenses:
        if expense["trip_id"] == trip_id:
            yield expense


def filter_by_category(expenses: list[dict], category: str) -> list[dict]:
    """Отобрать расходы указанной категории."""
    return [item for item in expenses if item["category"] == category]


def sort_expenses(expenses: list[dict], by: str = "amount") -> list[dict]:
    """Отсортировать расходы по сумме (по убыванию) или по дате."""
    if by == "date":
        return sorted(expenses, key=lambda item: item["date"])
    return sorted(expenses, key=lambda item: item["amount"], reverse=True)


def get_total(expenses: list[dict]) -> float:
    """Вернуть общую сумму расходов."""
    return round(sum(item["amount"] for item in expenses), 2)


def get_totals_by_category(expenses: list[dict]) -> dict[str, float]:
    """Вернуть словарь «категория → сумма расходов»."""
    totals: dict[str, float] = {}
    for expense in expenses:
        category = expense["category"]
        totals[category] = round(
            totals.get(category, 0.0) + expense["amount"], 2
        )
    return totals
