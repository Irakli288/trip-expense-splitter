"""Расчет долей, балансов и переводов между участниками."""

import math

from utils import format_money


def calculate_share(total_amount: float, participants_count: int) -> float:
    """Рассчитать долю одного участника в расходе (функция из ПР1).

    Доля округляется вверх до копеек, чтобы сумма долей
    гарантированно покрывала расход.
    """
    if participants_count <= 0:
        return 0.0
    return math.ceil(total_amount / participants_count * 100) / 100


def calculate_balance(paid_amount: float, share: float) -> float:
    """Вернуть баланс: сколько участник заплатил сверх доли (из ПР1)."""
    return round(paid_amount - share, 2)


def get_settlement_status(name: str, balance: float) -> str:
    """Сформировать текстовый статус расчета участника (из ПР1)."""
    if balance > 0:
        return f"{name}: ему должны вернуть {format_money(balance)}"
    elif balance < 0:
        return f"{name}: должен перевести {format_money(abs(balance))}"
    else:
        return f"{name}: расчет завершен"


def calculate_balances(
    expenses: list[dict],
    participant_ids: list[int]
) -> dict[int, float]:
    """Рассчитать баланс каждого участника по всем расходам поездки.

    Для каждого расхода плательщику засчитывается вся сумма,
    а каждому из split_between — его доля.
    """
    paid = dict.fromkeys(participant_ids, 0.0)
    owed = dict.fromkeys(participant_ids, 0.0)
    for expense in expenses:
        share = calculate_share(expense["amount"],
                                len(expense["split_between"]))
        paid[expense["payer_id"]] += expense["amount"]
        for participant_id in expense["split_between"]:
            owed[participant_id] += share
    return {
        participant_id: calculate_balance(paid[participant_id],
                                          owed[participant_id])
        for participant_id in participant_ids
    }


def make_transfers(balances: dict[int, float]) -> list[tuple[int, int, float]]:
    """Составить список переводов (кто, кому, сколько).

    Должники и получатели упорядочиваются по величине долга,
    и самый крупный должник переводит деньги самому крупному
    получателю, пока долги не будут закрыты. Копеечный остаток
    от округления долей вверх не переводится.
    """
    debtors = sorted(
        ([pid, -value] for pid, value in balances.items() if value < 0),
        key=lambda item: item[1], reverse=True
    )
    creditors = sorted(
        ([pid, value] for pid, value in balances.items() if value > 0),
        key=lambda item: item[1], reverse=True
    )
    transfers = []
    i = j = 0
    while i < len(debtors) and j < len(creditors):
        amount = round(min(debtors[i][1], creditors[j][1]), 2)
        if amount > 0:
            transfers.append((debtors[i][0], creditors[j][0], amount))
        debtors[i][1] = round(debtors[i][1] - amount, 2)
        creditors[j][1] = round(creditors[j][1] - amount, 2)
        if debtors[i][1] <= 0.01:
            i += 1
        if creditors[j][1] <= 0.01:
            j += 1
    return transfers
