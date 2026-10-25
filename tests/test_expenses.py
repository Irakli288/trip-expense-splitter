from datetime import date

import pytest

from models import Expense
from models.expenses import (
    add_expense,
    calculate_share,
    delete_expense,
    filter_by_category,
    get_totals_by_category,
    iter_trip_expenses,
    sort_expenses,
)
from utils import parse_amount


def test_parse_amount():
    assert parse_amount(" 99,90 ") == 99.9


def test_parse_amount_invalid():
    with pytest.raises(ValueError):
        parse_amount("abc")
    with pytest.raises(ValueError):
        parse_amount("-100")


def test_calculate_share():
    assert calculate_share(100, 3) == 33.34
    assert calculate_share(100, 0) == 0.0


def test_expense_creation(trip, people):
    ira, anna, max_ = people
    expense = Expense(1, trip, "Экскурсия", 3000, anna, [max_, anna, anna],
                      "развлечения", date(2026, 11, 5))
    assert expense.trip is trip
    assert expense.payer is anna
    assert expense.split_between == [anna, max_]
    assert expense.share == 1500
    assert expense.is_shared_with(max_)
    assert not expense.is_shared_with(ira)
    assert "оплатил Анна → делится: Анна, Максим" in str(expense)


def test_expense_invalid(trip, people):
    with pytest.raises(ValueError):
        Expense(1, trip, "Ужин", 0, people[0], people)
    with pytest.raises(ValueError):
        Expense(1, trip, "Ужин", 100, people[0], [])
    with pytest.raises(ValueError):
        Expense(1, trip, "Ужин", 100, people[0], people, "сувениры")
    assert not Expense.validate_category("сувениры")


def test_add_and_delete_expense(trip, people):
    expenses = []
    expense = add_expense(expenses, trip, "Аренда квартиры", 25500,
                          people[0], people, "жилье")
    assert expenses == [expense]
    assert list(iter_trip_expenses(expenses, trip)) == [expense]
    assert delete_expense(expenses, trip, 1) is expense
    assert expenses == []


def test_delete_missing_expense(trip):
    with pytest.raises(KeyError):
        delete_expense([], trip, 5)


def test_sort_filter_and_totals(trip, people):
    ira, anna, max_ = people
    expenses = []
    add_expense(expenses, trip, "Ужин", 4500, max_, people, "еда")
    add_expense(expenses, trip, "Обед", 1500, ira, [ira, anna], "еда")
    add_expense(expenses, trip, "Поезд", 18000, anna, people, "транспорт")
    assert sort_expenses(expenses)[0].title == "Поезд"
    assert len(filter_by_category(expenses, "еда")) == 2
    assert get_totals_by_category(expenses) == {"еда": 6000,
                                                "транспорт": 18000}
