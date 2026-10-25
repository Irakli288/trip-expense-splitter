import pytest

from expenses import (
    add_expense,
    delete_expense,
    get_totals_by_category,
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


def test_add_and_delete_expense():
    expenses = []
    add_expense(expenses, 1, "Аренда квартиры", 25500, 1, [1, 2, 3], "жилье")
    delete_expense(expenses, 1)
    assert expenses == []


def test_delete_missing_expense():
    with pytest.raises(KeyError):
        delete_expense([], 5)


def test_sort_and_totals():
    expenses = []
    add_expense(expenses, 1, "Ужин", 4500, 3, [1, 2, 3], "еда")
    add_expense(expenses, 1, "Обед", 1500, 1, [1, 2], "еда")
    add_expense(expenses, 1, "Поезд", 18000, 2, [1, 2, 3], "транспорт")
    assert sort_expenses(expenses)[0]["title"] == "Поезд"
    assert get_totals_by_category(expenses) == {"еда": 6000,
                                                "транспорт": 18000}
