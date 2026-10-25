from django.shortcuts import render

from models import Settlement
from models.expenses import get_total, iter_trip_expenses
from models.participants import get_trip_participants
from models.settlement import get_settlement_status
from models.trips import find_trip_by_id, sort_trips
from storage import load_all


def trips(request):
    trips_list, _, expenses_list = load_all()
    trip_rows = []
    for trip in sort_trips(trips_list):
        total = get_total(list(iter_trip_expenses(expenses_list, trip)))
        trip_rows.append({
            "trip": trip,
            "total": total,
            "budget_level": trip.budget_level(total),
        })
    context = {
        "trip_rows": trip_rows,
    }
    return render(request, "trips/trip_list.html", context)


def trip_detail(request, trip_id):
    trips_list, participants_list, expenses_list = load_all()
    trip = find_trip_by_id(trips_list, trip_id)
    context = {
        "trip": trip,
    }
    if trip is not None:
        expenses = list(iter_trip_expenses(expenses_list, trip))
        total = get_total(expenses)
        context.update({
            "participants": get_trip_participants(participants_list, trip),
            "expenses": expenses,
            "total": total,
            "budget_level": trip.budget_level(total),
            "budget_message": trip.check_budget(total),
        })
    return render(
        request,
        "trips/trip_detail.html",
        context,
        status=404 if trip is None else 200,
    )


def trip_settlement(request, trip_id):
    trips_list, participants_list, expenses_list = load_all()
    trip = find_trip_by_id(trips_list, trip_id)
    context = {
        "trip": trip,
    }
    if trip is not None:
        settlement = Settlement(
            trip,
            get_trip_participants(participants_list, trip),
            list(iter_trip_expenses(expenses_list, trip)),
        )
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
        status=404 if trip is None else 200,
    )
