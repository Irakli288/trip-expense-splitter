from django.http import HttpResponse

from homepage.views import page
from models import Settlement
from models.expenses import get_total, iter_trip_expenses
from models.participants import get_trip_participants
from models.settlement import get_settlement_status
from models.trips import find_trip_by_id, sort_trips
from storage import load_all
from utils import format_money


def trip_not_found():
    content = """
    <h1 class="text-danger">Поездка не найдена</h1>
    <a href="/trips/" class="btn btn-outline-secondary">
        ← к списку поездок
    </a>
    """
    return HttpResponse(page("Поездка не найдена", content), status=404)


def budget_badge(trip, total):
    if trip.budget <= 0:
        return "bg-secondary"
    if total > trip.budget:
        return "bg-danger"
    if total >= trip.budget * 0.8:
        return "bg-warning text-dark"
    return "bg-success"


def trips(request):
    trips_list, _, expenses_list = load_all()
    items = ""
    for trip in sort_trips(trips_list):
        total = get_total(list(iter_trip_expenses(expenses_list, trip)))
        items += f"""
        <a href="/trips/{trip.id}/"
           class="list-group-item list-group-item-action
                  d-flex justify-content-between align-items-center">
            <span>
                <strong>{trip.name}</strong><br>
                <small class="text-body-secondary">
                    {trip.start_date:%d.%m.%Y} – {trip.end_date:%d.%m.%Y},
                    {trip.duration} дн.
                </small>
            </span>
            <span class="badge {budget_badge(trip, total)}">
                {format_money(total)} из {format_money(trip.budget)}
            </span>
        </a>
        """
    content = f"""
    <h1>Поездки</h1>
    <div class="list-group">{items}</div>
    """
    return HttpResponse(page("Поездки", content))


def trip_detail(request, trip_id):
    trips_list, participants_list, expenses_list = load_all()
    trip = find_trip_by_id(trips_list, trip_id)
    if trip is None:
        return trip_not_found()

    participants = get_trip_participants(participants_list, trip)
    expenses = list(iter_trip_expenses(expenses_list, trip))
    total = get_total(expenses)

    people = "".join(
        f'<li class="list-group-item">{person.name}</li>'
        for person in participants
    ) or '<li class="list-group-item">Участников нет</li>'
    rows = "".join(
        f"""
        <tr>
            <td><a href="/expenses/{expense.id}/">{expense.title}</a></td>
            <td>{expense.category}</td>
            <td>{expense.payer.name}</td>
            <td class="text-end">{format_money(expense.amount)}</td>
        </tr>
        """
        for expense in expenses
    )

    content = f"""
    <div class="card mb-4">
        <div class="card-body">
            <h1 class="card-title h3">{trip.name}</h1>
            <p class="card-text">
                <strong>Даты:</strong>
                {trip.start_date:%d.%m.%Y} – {trip.end_date:%d.%m.%Y}
                ({trip.duration} дн.)
            </p>
            <p class="card-text">
                <strong>Потрачено:</strong> {format_money(total)}
                из {format_money(trip.budget)}
                <span class="badge {budget_badge(trip, total)}">
                    {trip.check_budget(total)}
                </span>
            </p>
            <a href="/trips/{trip.id}/settlement/" class="btn btn-primary">
                Кто кому должен
            </a>
            <a href="/trips/" class="btn btn-outline-secondary">
                ← к списку поездок
            </a>
        </div>
    </div>
    <div class="row g-4">
        <div class="col-md-4">
            <h2 class="h5">Участники</h2>
            <ul class="list-group">{people}</ul>
        </div>
        <div class="col-md-8">
            <h2 class="h5">Расходы</h2>
            <table class="table table-striped">
                <thead>
                    <tr>
                        <th>Расход</th>
                        <th>Категория</th>
                        <th>Оплатил</th>
                        <th class="text-end">Сумма</th>
                    </tr>
                </thead>
                <tbody>{rows}</tbody>
            </table>
        </div>
    </div>
    """
    return HttpResponse(page(trip.name, content))


def trip_settlement(request, trip_id):
    trips_list, participants_list, expenses_list = load_all()
    trip = find_trip_by_id(trips_list, trip_id)
    if trip is None:
        return trip_not_found()

    settlement = Settlement(
        trip,
        get_trip_participants(participants_list, trip),
        list(iter_trip_expenses(expenses_list, trip)),
    )
    statuses = ""
    for person, balance in settlement.get_balances().items():
        if balance > 0:
            badge = "bg-success"
        elif balance < 0:
            badge = "bg-danger"
        else:
            badge = "bg-secondary"
        statuses += f"""
        <li class="list-group-item d-flex justify-content-between">
            {get_settlement_status(person.name, balance)}
            <span class="badge {badge}">{format_money(balance)}</span>
        </li>
        """
    transfers = "".join(
        f'<li class="list-group-item">{debtor.name} → {creditor.name}: '
        f"<strong>{format_money(amount)}</strong></li>"
        for debtor, creditor, amount in settlement.get_transfers()
    ) or '<li class="list-group-item">Переводы не нужны</li>'

    content = f"""
    <h1>Расчет: {trip.name}</h1>
    <div class="row g-4 mb-4">
        <div class="col-md-6">
            <h2 class="h5">Балансы участников</h2>
            <ul class="list-group">{statuses}</ul>
        </div>
        <div class="col-md-6">
            <h2 class="h5">Переводы</h2>
            <ul class="list-group">{transfers}</ul>
        </div>
    </div>
    <a href="/trips/{trip.id}/" class="btn btn-outline-secondary">
        ← к поездке
    </a>
    """
    return HttpResponse(page(f"Расчет – {trip.name}", content))
