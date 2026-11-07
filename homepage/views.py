from decimal import Decimal

from django.db.models import Count, Max, Sum
from django.db.models.functions import Coalesce
from django.shortcuts import render

from expenses.models import Expense
from trips.models import Participant, Trip


def index(request):
    # Общие цифры по сервису: одной строкой aggregate() по расходам
    # и простым подсчетом поездок и участников.
    summary = Expense.objects.aggregate(
        expenses_count=Count("pk"),
        expenses_total=Coalesce(Sum("amount"), Decimal("0")),
        max_amount=Max("amount"),
    )
    summary["trips_count"] = Trip.objects.count()
    summary["participants_count"] = Participant.objects.count()
    return render(request, "homepage/index.html", {"summary": summary})
