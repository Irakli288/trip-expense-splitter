"""Класс Settlement: доли, балансы и переводы между участниками."""

from utils import format_money

from .expenses import Expense
from .participants import Participant
from .trips import Trip


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


def make_transfers(
    balances: dict[Participant, float],
) -> list[tuple[Participant, Participant, float]]:
    """Составить список переводов (кто, кому, сколько).

    Должники и получатели упорядочиваются по величине долга,
    и самый крупный должник переводит деньги самому крупному
    получателю, пока долги не будут закрыты. Копеечный остаток
    от округления долей вверх не переводится.
    """
    debtors = sorted(
        ([person, -value] for person, value in balances.items() if value < 0),
        key=lambda item: item[1], reverse=True
    )
    creditors = sorted(
        ([person, value] for person, value in balances.items() if value > 0),
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


class Settlement:
    """Итоговый расчет поездки по ее участникам и расходам."""

    def __init__(
        self,
        trip: Trip,
        participants: list[Participant],
        expenses: list[Expense],
    ) -> None:
        """Создать расчет для поездки, ее участников и расходов."""
        self.trip = trip
        self.participants = participants
        self.expenses = expenses

    def get_balances(self) -> dict[Participant, float]:
        """Рассчитать баланс каждого участника по всем расходам.

        Плательщику засчитывается вся сумма расхода,
        а каждому из split_between — его доля.
        """
        paid = dict.fromkeys(self.participants, 0.0)
        owed = dict.fromkeys(self.participants, 0.0)
        for expense in self.expenses:
            paid[expense.payer] += expense.amount
            for participant in expense.split_between:
                owed[participant] += expense.share
        return {
            participant: calculate_balance(paid[participant],
                                           owed[participant])
            for participant in self.participants
        }

    def get_transfers(self) -> list[tuple[Participant, Participant, float]]:
        """Вернуть переводы, закрывающие долги участников."""
        return make_transfers(self.get_balances())

    def __str__(self) -> str:
        """Вернуть статусы участников и список переводов."""
        lines = [get_settlement_status(participant.name, balance)
                 for participant, balance in self.get_balances().items()]
        transfers = self.get_transfers()
        if transfers:
            lines.append("\nПереводы:")
            for debtor, creditor, amount in transfers:
                lines.append(f"  {debtor.name} → {creditor.name}: "
                             f"{format_money(amount)}")
        return "\n".join(lines)
