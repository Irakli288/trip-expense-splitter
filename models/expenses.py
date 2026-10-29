"""Класс Expense и функции для работы с расходами поездки."""

import math
from collections.abc import Iterator
from datetime import date

from utils import format_money

from .participants import Participant
from .trips import Trip

CATEGORIES = ("жилье", "транспорт", "еда", "развлечения", "прочее")


def calculate_share(total_amount: float, participants_count: int) -> float:
    """Считает, сколько должен заплатить один участник.

    Доля округляется вверх до копеек, чтобы в сумме доли
    точно покрыли весь расход.
    """
    if participants_count <= 0:
        return 0.0
    return math.ceil(total_amount / participants_count * 100) / 100


class Expense:
    """Расход в поездке: кто заплатил и на кого он делится."""

    def __init__(
        self,
        expense_id: int,
        trip: Trip,
        title: str,
        amount: float,
        payer: Participant,
        split_between: list[Participant],
        category: str = "прочее",
        expense_date: date | None = None,
    ) -> None:
        """Создает расход. Если данные неправильные, будет ValueError.

        split_between — это те, на кого делится расход.
        Тот, кто платил, не обязательно входит в этот список.
        """
        if amount <= 0:
            raise ValueError("Сумма расхода должна быть больше нуля")
        if not split_between:
            raise ValueError(
                "Расход должен делиться хотя бы на одного участника"
            )
        if not Expense.validate_category(category):
            raise ValueError(f"Неизвестная категория: {category}")
        self.id = expense_id
        self.trip = trip
        self.title = title
        self.amount = amount
        self.payer = payer
        unique = {participant.id: participant for participant in split_between}
        self.split_between = [unique[key] for key in sorted(unique)]
        self.category = category
        self.date = expense_date or date.today()

    @staticmethod
    def validate_category(category: str) -> bool:
        """Проверяет, что такая категория есть в CATEGORIES."""
        return category in CATEGORIES

    @property
    def share(self) -> float:
        """Сколько приходится на одного участника в этом расходе."""
        return calculate_share(self.amount, len(self.split_between))

    def is_shared_with(self, participant: Participant) -> bool:
        """Проверяет, делится ли расход на этого участника."""
        return participant in self.split_between

    def __str__(self) -> str:
        """Возвращает строку с суммой, категорией, плательщиком и долями."""
        split = ", ".join(item.name for item in self.split_between)
        return (f"{self.title:<22} {format_money(self.amount):>14}  "
                f"[{self.category}] оплатил {self.payer.name}"
                f" → делится: {split}")


def add_expense(
    expenses: list[Expense],
    trip: Trip,
    title: str,
    amount: float,
    payer: Participant,
    split_between: list[Participant],
    category: str = "прочее",
    expense_date: date | None = None,
) -> Expense:
    """Создает расход, добавляет его в список и возвращает."""
    expense_id = max((item.id for item in expenses), default=0) + 1
    expense = Expense(expense_id, trip, title, amount, payer,
                      split_between, category, expense_date)
    expenses.append(expense)
    return expense


def find_expense_by_id(
    expenses: list[Expense],
    expense_id: int,
) -> Expense | None:
    """Возвращает расход с таким номером или None, если его нет."""
    for expense in expenses:
        if expense.id == expense_id:
            return expense
    return None


def delete_expense(
    expenses: list[Expense],
    trip: Trip,
    expense_id: int,
) -> Expense:
    """Удаляет расход поездки по номеру и возвращает его.

    Если такого расхода в поездке нет, будет KeyError.
    """
    for index, expense in enumerate(expenses):
        if expense.id == expense_id and expense.trip is trip:
            return expenses.pop(index)
    raise KeyError(f"В поездке нет расхода № {expense_id}")


def iter_trip_expenses(
    expenses: list[Expense],
    trip: Trip,
) -> Iterator[Expense]:
    """Генератор, который по одному отдает расходы нужной поездки."""
    for expense in expenses:
        if expense.trip is trip:
            yield expense


def filter_by_category(
    expenses: list[Expense],
    category: str,
) -> list[Expense]:
    """Оставляет только расходы нужной категории."""
    return [item for item in expenses if item.category == category]


def sort_expenses(
    expenses: list[Expense],
    by: str = "amount",
) -> list[Expense]:
    """Сортирует расходы по сумме (от большей к меньшей) или по дате."""
    if by == "date":
        return sorted(expenses, key=lambda item: item.date)
    return sorted(expenses, key=lambda item: item.amount, reverse=True)


def get_total(expenses: list[Expense]) -> float:
    """Считает общую сумму расходов."""
    return round(sum(item.amount for item in expenses), 2)


def get_totals_by_category(expenses: list[Expense]) -> dict[str, float]:
    """Возвращает словарь «категория → сколько потрачено»."""
    totals: dict[str, float] = {}
    for expense in expenses:
        totals[expense.category] = round(
            totals.get(expense.category, 0.0) + expense.amount, 2
        )
    return totals


def show_expenses(expenses: list[Expense]) -> None:
    """Печатает расходы и итоги по категориям."""
    if not expenses:
        print("Расходов нет")
        return
    for expense in expenses:
        print(f"{expense.id:>3}. {expense}")
    print(f"Итого: {format_money(get_total(expenses))}")
    for category, total in get_totals_by_category(expenses).items():
        print(f"  {category}: {format_money(total)}")
