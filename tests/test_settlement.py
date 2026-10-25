from expenses import add_expense
from settlement import (
    calculate_balances,
    calculate_share,
    get_settlement_status,
    make_transfers,
)


def test_calculate_share():
    assert calculate_share(100, 3) == 33.34
    assert calculate_share(100, 0) == 0.0


def test_settlement_status():
    assert "вернуть 17000.00" in get_settlement_status("Ираклий", 17000)


def test_balances_and_transfers():
    expenses = []
    add_expense(expenses, 1, "Аренда квартиры", 25500, 1, [1, 2, 3])
    add_expense(expenses, 1, "Билеты на поезд", 18000, 2, [1, 2, 3])
    balances = calculate_balances(expenses, [1, 2, 3])
    assert balances == {1: 11000.0, 2: 3500.0, 3: -14500.0}
    assert make_transfers(balances) == [(3, 1, 11000.0), (3, 2, 3500.0)]
