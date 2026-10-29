"""Мелкие помощники: разбор сумм и дат, ввод с проверкой."""

from datetime import date, datetime

CURRENCY = "₽"
DATE_FORMAT = "%d.%m.%Y"


def parse_amount(text: str) -> float:
    """Превращает строку с суммой в число.

    Дробную часть можно отделять запятой или точкой.
    Если сумма записана неправильно, будет ValueError.
    """
    cleaned = text.strip().replace(",", ".")
    amount = float(cleaned)
    if amount <= 0:
        raise ValueError("Сумма должна быть больше нуля")
    return round(amount, 2)


def parse_date(text: str) -> date:
    """Превращает строку вида ДД.ММ.ГГГГ в дату."""
    return datetime.strptime(text.strip(), DATE_FORMAT).date()


def format_money(amount: float) -> str:
    """Возвращает сумму строкой с двумя знаками после запятой и валютой."""
    return f"{amount:.2f} {CURRENCY}"


def input_text(prompt: str) -> str:
    """Спрашивает непустую строку, пока ее не введут."""
    while True:
        text = input(prompt).strip()
        if text:
            return text
        print("Значение не может быть пустым")


def input_int(prompt: str) -> int:
    """Спрашивает целое число, пока не введут правильно."""
    while True:
        try:
            return int(input(prompt))
        except ValueError:
            print("Ошибка: введите целое число")


def input_amount(prompt: str) -> float:
    """Спрашивает положительную сумму, пока не введут правильно."""
    while True:
        try:
            return parse_amount(input(prompt))
        except ValueError:
            print("Ошибка: введите сумму больше нуля, например 1500 или 99,90")


def input_date(prompt: str) -> date:
    """Спрашивает дату в формате ДД.ММ.ГГГГ, пока не введут правильно."""
    while True:
        try:
            return parse_date(input(prompt))
        except ValueError:
            print("Ошибка: введите дату в формате ДД.ММ.ГГГГ")


def input_ids(prompt: str) -> list[int]:
    """Спрашивает номера через запятую, пустой ввод значит «все»."""
    while True:
        text = input(prompt).strip()
        if not text:
            return []
        try:
            return [int(part) for part in text.split(",")]
        except ValueError:
            print("Ошибка: введите номера через запятую, например 1, 3")
