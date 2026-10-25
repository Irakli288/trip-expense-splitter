"""Вспомогательные функции: разбор сумм и дат, безопасный ввод."""

from datetime import date, datetime

CURRENCY = "₽"
DATE_FORMAT = "%d.%m.%Y"


def parse_amount(text: str) -> float:
    """Преобразовать строку с суммой в число float.

    Принимает запятую или точку как разделитель дробной части.
    Функция перенесена из ПР1; теперь при некорректной сумме
    она не возвращает -1.0, а выбрасывает ValueError.
    """
    cleaned = text.strip().replace(",", ".")
    amount = float(cleaned)
    if amount <= 0:
        raise ValueError("Сумма должна быть больше нуля")
    return round(amount, 2)


def parse_date(text: str) -> date:
    """Преобразовать строку вида ДД.ММ.ГГГГ в объект date."""
    return datetime.strptime(text.strip(), DATE_FORMAT).date()


def format_money(amount: float) -> str:
    """Вернуть сумму в виде строки с двумя знаками и валютой."""
    return f"{amount:.2f} {CURRENCY}"


def input_text(prompt: str) -> str:
    """Запросить непустую строку; пустой ввод повторяет запрос."""
    while True:
        text = input(prompt).strip()
        if text:
            return text
        print("Значение не может быть пустым")


def input_int(prompt: str) -> int:
    """Запросить целое число; при ошибке запрос повторяется."""
    while True:
        try:
            return int(input(prompt))
        except ValueError:
            print("Ошибка: введите целое число")


def input_amount(prompt: str) -> float:
    """Запросить положительную сумму; при ошибке запрос повторяется."""
    while True:
        try:
            return parse_amount(input(prompt))
        except ValueError:
            print("Ошибка: введите сумму больше нуля, например 1500 или 99,90")


def input_date(prompt: str) -> date:
    """Запросить дату в формате ДД.ММ.ГГГГ; при ошибке запрос повторяется."""
    while True:
        try:
            return parse_date(input(prompt))
        except ValueError:
            print("Ошибка: введите дату в формате ДД.ММ.ГГГГ")


def input_ids(prompt: str) -> list[int]:
    """Запросить номера через запятую; пустой ввод означает «все»."""
    while True:
        text = input(prompt).strip()
        if not text:
            return []
        try:
            return [int(part) for part in text.split(",")]
        except ValueError:
            print("Ошибка: введите номера через запятую, например 1, 3")
