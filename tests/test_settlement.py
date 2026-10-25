from models import Settlement
from models.expenses import add_expense
from models.settlement import get_settlement_status, make_transfers


def test_settlement_status():
    assert "вернуть 17000.00" in get_settlement_status("Ираклий", 17000)
    assert "перевести 500.00" in get_settlement_status("Анна", -500)
    assert "завершен" in get_settlement_status("Максим", 0)


def test_balances_and_transfers(trip, people):
    ira, anna, max_ = people
    expenses = []
    add_expense(expenses, trip, "Аренда квартиры", 25500, ira, people)
    add_expense(expenses, trip, "Билеты на поезд", 18000, anna, people)
    settlement = Settlement(trip, people, expenses)
    balances = settlement.get_balances()
    assert balances == {ira: 11000.0, anna: 3500.0, max_: -14500.0}
    assert make_transfers(balances) == [(max_, ira, 11000.0),
                                        (max_, anna, 3500.0)]
    assert settlement.get_transfers() == make_transfers(balances)


def test_settlement_str(trip, people):
    ira, anna, max_ = people
    expenses = []
    add_expense(expenses, trip, "Аренда квартиры", 3000, ira, people)
    text = str(Settlement(trip, people, expenses))
    assert "Ираклий: ему должны вернуть 2000.00" in text
    assert "Анна → Ираклий: 1000.00" in text
