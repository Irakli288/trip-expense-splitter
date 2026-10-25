"""Сервис распределения расходов поездки — консольное приложение (ПР2).

Данные поездок, участников и расходов хранятся в JSON-файлах каталога
data/ и загружаются при запуске. Меню позволяет выбрать поездку,
добавлять участников и расходы и получать итоговый расчет:
кто, кому и сколько должен перевести.
"""

from datetime import date

import storage
from expenses import (
    CATEGORIES,
    add_expense,
    delete_expense,
    filter_by_category,
    get_total,
    get_totals_by_category,
    iter_trip_expenses,
    sort_expenses,
)
from participants import add_participant, get_names, get_trip_participants
from settlement import (
    calculate_balances,
    get_settlement_status,
    make_transfers,
)
from trips import (
    add_trip,
    check_budget,
    get_trip,
    get_trip_duration,
    sort_trips,
)
from utils import (
    format_money,
    input_amount,
    input_date,
    input_ids,
    input_int,
    input_text,
)

MENU = """
=== Сервис распределения расходов поездки ===
Текущая поездка: {trip}

1. Показать поездки
2. Создать поездку
3. Выбрать поездку
4. Показать участников
5. Добавить участника
6. Показать расходы
7. Добавить расход
8. Удалить расход
9. Проверить бюджет
10. Рассчитать, кто кому должен
0. Выход
"""


def show_trips(trips: dict[int, dict]) -> None:
    """Вывести список поездок, упорядоченный по дате начала."""
    if not trips:
        print("Поездок пока нет")
        return
    for trip in sort_trips(trips):
        start = date.fromisoformat(trip["start_date"])
        end = date.fromisoformat(trip["end_date"])
        print(f"{trip['id']:>3}. {trip['name']:<25} "
              f"{start:%d.%m.%Y} – {end:%d.%m.%Y} "
              f"({get_trip_duration(start, end)} дн.), "
              f"бюджет {format_money(trip['budget'])}")


def show_participants(participants: list[dict]) -> None:
    """Вывести участников поездки."""
    if not participants:
        print("В поездке нет участников")
        return
    for participant in participants:
        print(f"{participant['id']:>3}. {participant['name']}")


def show_expenses(expenses: list[dict], names: dict[int, str]) -> None:
    """Вывести расходы в виде таблицы и итог по категориям."""
    if not expenses:
        print("Расходов нет")
        return
    for expense in expenses:
        split = ", ".join(names[pid] for pid in expense["split_between"])
        print(f"{expense['id']:>3}. {expense['title']:<22} "
              f"{format_money(expense['amount']):>14}  "
              f"[{expense['category']}] оплатил {names[expense['payer_id']]}"
              f" → делится: {split}")
    print(f"Итого: {format_money(get_total(expenses))}")
    for category, total in get_totals_by_category(expenses).items():
        print(f"  {category}: {format_money(total)}")


def show_settlement(expenses: list[dict], names: dict[int, str]) -> None:
    """Вывести балансы участников и список переводов."""
    balances = calculate_balances(expenses, list(names))
    for participant_id, balance in balances.items():
        print(get_settlement_status(names[participant_id], balance))
    transfers = make_transfers(balances)
    if transfers:
        print("\nПереводы:")
        for debtor, creditor, amount in transfers:
            print(f"  {names[debtor]} → {names[creditor]}: "
                  f"{format_money(amount)}")


def create_trip(trips: dict[int, dict]) -> int:
    """Запросить данные новой поездки, сохранить ее и вернуть номер."""
    name = input_text("Название поездки: ")
    start_date = input_date("Дата начала (ДД.ММ.ГГГГ): ")
    end_date = input_date("Дата окончания (ДД.ММ.ГГГГ): ")
    budget = input_amount("Бюджет: ")
    trip = add_trip(trips, name, start_date, end_date, budget)
    storage.save_trips(trips)
    print(f"Создана поездка № {trip['id']}")
    return trip["id"]


def create_expense(
    expenses: list[dict],
    trip_id: int,
    names: dict[int, str]
) -> None:
    """Запросить данные расхода, проверить участников и сохранить."""
    title = input_text("Название расхода: ")
    amount = input_amount("Сумма: ")
    print("Категории: " + ", ".join(CATEGORIES))
    category = input("Категория [прочее]: ").strip().lower() or "прочее"
    show_participants([{"id": pid, "name": name}
                       for pid, name in names.items()])
    payer_id = input_int("Кто оплатил (номер): ")
    split_between = input_ids("Между кем делить (номера через запятую, "
                              "Enter — между всеми): ") or list(names)
    unknown = {payer_id, *split_between} - set(names)
    if unknown:
        raise KeyError(f"Нет участников с номерами {sorted(unknown)}")
    expense = add_expense(expenses, trip_id, title, amount, payer_id,
                          split_between, category)
    storage.save_expenses(expenses)
    print(f"Добавлен расход № {expense['id']}")


def main() -> None:
    """Точка запуска: загрузка данных и цикл меню."""
    trips = storage.load_trips()
    participants = storage.load_participants()
    expenses = storage.load_expenses()
    current_id = min(trips, default=0)

    while True:
        current_trip = trips.get(current_id)
        print(MENU.format(
            trip=current_trip["name"] if current_trip else "не выбрана"
        ))
        choice = input("Выберите действие: ").strip()
        if choice == "0":
            print("До свидания!")
            break
        if choice not in {str(number) for number in range(1, 11)}:
            print("Нет такого пункта меню")
            continue
        try:
            if choice == "1":
                show_trips(trips)
                continue
            if choice == "2":
                current_id = create_trip(trips)
                continue
            if choice == "3":
                trip_id = input_int("Номер поездки: ")
                current_id = get_trip(trips, trip_id)["id"]
                continue
            trip = get_trip(trips, current_id)
            trip_participants = get_trip_participants(participants, trip["id"])
            names = get_names(trip_participants)
            trip_expenses = list(iter_trip_expenses(expenses, trip["id"]))

            if choice == "4":
                show_participants(trip_participants)
            elif choice == "5":
                add_participant(participants, trip["id"],
                                input_text("Имя участника: "))
                storage.save_participants(participants)
                print("Участник добавлен")
            elif choice == "6":
                category = input("Категория (Enter — все): ").strip().lower()
                if category:
                    trip_expenses = filter_by_category(trip_expenses, category)
                show_expenses(sort_expenses(trip_expenses), names)
            elif choice == "7":
                if not names:
                    print("Сначала добавьте участников")
                    continue
                create_expense(expenses, trip["id"], names)
            elif choice == "8":
                expense_ids = {item["id"] for item in trip_expenses}
                expense_id = input_int("Номер расхода: ")
                if expense_id not in expense_ids:
                    raise KeyError(f"В поездке нет расхода № {expense_id}")
                removed = delete_expense(expenses, expense_id)
                storage.save_expenses(expenses)
                print(f"Удален расход «{removed['title']}»")
            elif choice == "9":
                total = get_total(trip_expenses)
                print(f"Потрачено {format_money(total)} из "
                      f"{format_money(trip['budget'])}")
                print(check_budget(total, trip["budget"]))
            elif choice == "10":
                show_settlement(trip_expenses, names)
        except (KeyError, ValueError, OSError) as error:
            message = error.args[0] if error.args else error
            print(f"Ошибка: {message}")


if __name__ == "__main__":
    main()
