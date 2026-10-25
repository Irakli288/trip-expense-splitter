"""Сервис распределения расходов поездки — начальный сценарий (ПР1).

Сценарий: трое друзей едут в поездку. Один участник оплачивает общий
расход (например, аренду жилья). Программа считает долю каждого,
проверяет бюджет поездки и формирует расчет: кто кому сколько должен.

На ПР1 используются только простые типы данных, операции,
преобразование типов, ветвления, функции и импорт модулей.
Коллекции, циклы и классы появятся в ПР2 и ПР3.
"""

import math
from datetime import date

CURRENCY = "₽"


def get_trip_duration(start_date, end_date):
    """Возвращает длительность поездки в днях (включая оба дня).

    Если дата окончания раньше даты начала, возвращает 0.
    """
    if end_date < start_date:
        return 0
    return (end_date - start_date).days + 1


def parse_amount(text):
    """Преобразует строку с суммой в число float.

    Принимает запятую или точку как разделитель дробной части.
    Возвращает -1.0, если строка не является корректной
    неотрицательной суммой.
    """
    cleaned = text.strip().replace(",", ".")
    if cleaned == "":
        return -1.0
    if cleaned.replace(".", "", 1).isdigit():
        return float(cleaned)
    return -1.0


def calculate_share(total_amount, participants_count):
    """Рассчитывает долю одного участника в общем расходе.

    Доля округляется вверх до копеек, чтобы сумма долей
    гарантированно покрывала расход.
    """
    if participants_count <= 0:
        return 0.0
    return math.ceil(total_amount / participants_count * 100) / 100


def calculate_balance(paid_amount, share):
    """Возвращает баланс участника: сколько он заплатил сверх своей доли.

    Положительный баланс — участнику должны вернуть деньги,
    отрицательный — участник должен доплатить.
    """
    return round(paid_amount - share, 2)


def get_settlement_status(name, balance):
    """Формирует текстовый статус расчета для участника."""
    if balance > 0:
        return f"{name}: ему должны вернуть {balance:.2f} {CURRENCY}"
    elif balance < 0:
        return f"{name}: должен перевести {abs(balance):.2f} {CURRENCY}"
    else:
        return f"{name}: расчет завершен"


def check_budget(total_amount, budget):
    """Сравнивает сумму расходов с бюджетом поездки."""
    if budget <= 0:
        return "Бюджет не задан"
    used_percent = int(total_amount / budget * 100)
    if total_amount > budget:
        return f"Бюджет превышен на {total_amount - budget:.2f} {CURRENCY}"
    elif used_percent >= 80:
        return f"Внимание: израсходовано {used_percent}% бюджета"
    else:
        return f"Расходы в пределах бюджета ({used_percent}%)"


def main():
    # Поездка
    trip_name = "Поездка в Казань"
    start_date = date(2026, 11, 3)
    end_date = date(2026, 11, 6)
    budget = parse_amount("30000")

    # Участники
    participant_1 = "Ираклий"
    participant_2 = "Анна"
    participant_3 = "Максим"
    participants_count = 3

    # Расход: строка, как если бы ее ввел пользователь
    expense_title = "Аренда квартиры"
    expense_amount = parse_amount("25500")
    payer = participant_1

    print(f"Поездка: {trip_name}")
    print(f"Даты: {start_date:%d.%m.%Y} – {end_date:%d.%m.%Y} "
          f"({get_trip_duration(start_date, end_date)} дн.)")
    print(f"Участники: {participant_1}, {participant_2}, {participant_3}")
    print()

    if expense_amount < 0:
        print("Ошибка: некорректная сумма расхода")
        return

    print(f"Расход: {expense_title} — {expense_amount:.2f} {CURRENCY}, "
          f"оплатил {payer}")
    print(check_budget(expense_amount, budget))
    print()

    # Расчет
    share = calculate_share(expense_amount, participants_count)
    print(f"Доля каждого участника: {share:.2f} {CURRENCY}")

    paid_1 = expense_amount if payer == participant_1 else 0.0
    paid_2 = expense_amount if payer == participant_2 else 0.0
    paid_3 = expense_amount if payer == participant_3 else 0.0

    print(get_settlement_status(participant_1,
                                calculate_balance(paid_1, share)))
    print(get_settlement_status(participant_2,
                                calculate_balance(paid_2, share)))
    print(get_settlement_status(participant_3,
                                calculate_balance(paid_3, share)))


if __name__ == "__main__":
    main()
