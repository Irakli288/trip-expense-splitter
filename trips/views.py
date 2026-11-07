from django.shortcuts import redirect, render

import models as domain
from models.settlement import get_settlement_status
from expenses.choices import Status
from splitter.search import text_search

from .models import Trip


def trips(request):
    # Поиск поездки по части названия: ?q=казань.
    query = request.GET.get("q", "").strip()
    trips_data = Trip.objects.with_totals()
    if query:
        trips_data = trips_data.filter(text_search(query, "name"))
    context = {"trips": trips_data, "query": query}
    return render(request, "trips/trip_list.html", context)


def trip_by_id(request, trip_id):
    """Старые адреса /trips/1/ ведут на новые /trips/poezdka-v-kazan/."""
    trip = Trip.objects.filter(pk=trip_id).only("slug").first()
    if trip is None:
        return render(request, "trips/trip_detail.html", status=404)
    return redirect(trip, permanent=True)


def trip_detail(request, slug):
    trip = Trip.objects.with_totals().filter(slug=slug).first()
    context = {"trip": trip}
    if trip is not None:
        context.update({
            "participants": trip.participants.all(),
            # select_related("payer") забирает плательщика тем же запросом,
            # иначе на каждую строку таблицы был бы еще один запрос.
            # Отмененные расходы тоже показываем, но серым цветом.
            "expenses": trip.expenses.select_related("payer"),
            # Участники, которые не оплатили ни одного действующего расхода.
            "not_paid": trip.participants.exclude(
                paid_expenses__status=Status.ACTIVE
            ),
        })
    return render(
        request,
        "trips/trip_detail.html",
        context,
        status=404 if trip is None else 200,
    )


def load_settlement(record):
    """Собирает объект Settlement из ПР3 по поездке из базы.

    Балансы и переводы по-прежнему считает класс Settlement, поэтому
    записи моделей Django превращаются в объекты Trip, Participant
    и Expense из пакета models. Отмененные расходы в расчет не входят.
    """
    trip = domain.Trip(
        record.pk,
        record.name,
        record.start_date,
        record.end_date,
        float(record.budget or 0),
    )
    participants = {
        person.pk: domain.Participant(person.pk, person.name, trip)
        for person in record.participants.all()
    }
    # prefetch_related подгружает участников всех расходов одним
    # запросом, а не отдельным запросом на каждый расход.
    expenses = [
        domain.Expense(
            item.pk,
            trip,
            item.title,
            float(item.amount),
            participants[item.payer_id],
            [participants[person.pk] for person in item.split_between.all()],
            item.category,
            item.expense_date,
        )
        for item in record.expenses.active().prefetch_related(
            "split_between"
        )
    ]
    return domain.Settlement(trip, list(participants.values()), expenses)


def trip_settlement(request, slug):
    record = Trip.objects.filter(slug=slug).first()
    context = {"trip": record}
    if record is not None:
        settlement = load_settlement(record)
        context["balances"] = [
            {
                "participant": person,
                "balance": balance,
                "status": get_settlement_status(person.name, balance),
            }
            for person, balance in settlement.get_balances().items()
        ]
        context["transfers"] = settlement.get_transfers()
    return render(
        request,
        "trips/trip_settlement.html",
        context,
        status=404 if record is None else 200,
    )
