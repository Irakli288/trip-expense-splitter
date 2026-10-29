"""Консольная версия сервиса для деления расходов в поездке.

Все строится на объектах Trip, Participant, Expense и Settlement.
При запуске данные из папки data/ превращаются в списки объектов,
меню передает их функциям из пакета models, а storage.py
сохраняет изменения обратно в JSON.
"""

import storage
from models import Expense, Participant, Settlement, Trip
from models.expenses import (
    CATEGORIES,
    add_expense,
    delete_expense,
    filter_by_category,
    get_total,
    iter_trip_expenses,
    show_expenses,
    sort_expenses,
)
from models.participants import (
    add_participant,
    find_participant_by_id,
    get_trip_participants,
    show_participants,
)
from models.trips import add_trip, get_trip, show_trips
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


def create_trip(trips: list[Trip]) -> Trip:
    """Спрашивает данные новой поездки, сохраняет ее и возвращает."""
    name = input_text("Название поездки: ")
    start_date = input_date("Дата начала (ДД.ММ.ГГГГ): ")
    end_date = input_date("Дата окончания (ДД.ММ.ГГГГ): ")
    budget = input_amount("Бюджет: ")
    trip = add_trip(trips, name, start_date, end_date, budget)
    storage.save_trips(trips)
    print(f"Создана поездка № {trip.id}")
    return trip


def select_participant(
    participants: list[Participant],
    participant_id: int,
) -> Participant:
    """Ищет участника поездки по номеру, если нет такого, то KeyError."""
    participant = find_participant_by_id(participants, participant_id)
    if participant is None:
        raise KeyError(f"В поездке нет участника № {participant_id}")
    return participant


def create_expense(
    expenses: list[Expense],
    trip: Trip,
    participants: list[Participant],
) -> None:
    """Спрашивает данные расхода, находит участников и сохраняет расход."""
    title = input_text("Название расхода: ")
    amount = input_amount("Сумма: ")
    print("Категории: " + ", ".join(CATEGORIES))
    category = input("Категория [прочее]: ").strip().lower() or "прочее"
    show_participants(participants)
    payer = select_participant(participants,
                               input_int("Кто оплатил (номер): "))
    split_ids = input_ids("Между кем делить (номера через запятую, "
                          "Enter — между всеми): ")
    split_between = [select_participant(participants, participant_id)
                     for participant_id in split_ids] or participants
    expense = add_expense(expenses, trip, title, amount, payer,
                          split_between, category)
    storage.save_expenses(expenses)
    print(f"Добавлен расход № {expense.id}")


def main() -> None:
    """Точка входа: загружает объекты из JSON и крутит меню."""
    trips = storage.load_trips()
    participants = storage.load_participants(trips)
    expenses = storage.load_expenses(trips, participants)
    current_trip = min(trips, key=lambda trip: trip.id, default=None)

    while True:
        print(MENU.format(
            trip=current_trip.name if current_trip else "не выбрана"
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
                current_trip = create_trip(trips)
                continue
            if choice == "3":
                current_trip = get_trip(trips, input_int("Номер поездки: "))
                continue
            if current_trip is None:
                raise KeyError("Сначала создайте или выберите поездку")
            trip = current_trip
            trip_participants = get_trip_participants(participants, trip)
            trip_expenses = list(iter_trip_expenses(expenses, trip))

            if choice == "4":
                show_participants(trip_participants)
            elif choice == "5":
                add_participant(participants, trip,
                                input_text("Имя участника: "))
                storage.save_participants(participants)
                print("Участник добавлен")
            elif choice == "6":
                category = input("Категория (Enter — все): ").strip().lower()
                if category:
                    trip_expenses = filter_by_category(trip_expenses, category)
                show_expenses(sort_expenses(trip_expenses))
            elif choice == "7":
                if not trip_participants:
                    print("Сначала добавьте участников")
                    continue
                create_expense(expenses, trip, trip_participants)
            elif choice == "8":
                removed = delete_expense(expenses, trip,
                                         input_int("Номер расхода: "))
                storage.save_expenses(expenses)
                print(f"Удален расход «{removed.title}»")
            elif choice == "9":
                total = get_total(trip_expenses)
                print(f"Потрачено {format_money(total)} из "
                      f"{format_money(trip.budget)}")
                print(trip.check_budget(total))
            elif choice == "10":
                print(Settlement(trip, trip_participants, trip_expenses))
        except (KeyError, ValueError, OSError) as error:
            message = error.args[0] if error.args else error
            print(f"Ошибка: {message}")


if __name__ == "__main__":
    main()
