from datetime import date

from main import (
    calculate_balance,
    calculate_share,
    check_budget,
    get_settlement_status,
    get_trip_duration,
    parse_amount,
)


def test_trip_duration():
    assert get_trip_duration(date(2026, 11, 3), date(2026, 11, 6)) == 4


def test_trip_duration_wrong_dates():
    assert get_trip_duration(date(2026, 11, 6), date(2026, 11, 3)) == 0


def test_parse_amount():
    assert parse_amount("1500") == 1500.0
    assert parse_amount(" 99,90 ") == 99.9


def test_parse_amount_invalid():
    assert parse_amount("") == -1.0
    assert parse_amount("abc") == -1.0
    assert parse_amount("-100") == -1.0


def test_calculate_share():
    assert calculate_share(25500, 3) == 8500.0
    assert calculate_share(100, 3) == 33.34
    assert calculate_share(100, 0) == 0.0


def test_calculate_balance():
    assert calculate_balance(25500, 8500) == 17000.0
    assert calculate_balance(0, 8500) == -8500.0


def test_settlement_status():
    assert "вернуть 17000.00" in get_settlement_status("Ираклий", 17000)
    assert "перевести 8500.00" in get_settlement_status("Анна", -8500)
    assert "завершен" in get_settlement_status("Максим", 0)


def test_check_budget():
    assert "превышен" in check_budget(31000, 30000)
    assert "Внимание" in check_budget(25500, 30000)
    assert "пределах" in check_budget(10000, 30000)
    assert check_budget(100, 0) == "Бюджет не задан"
