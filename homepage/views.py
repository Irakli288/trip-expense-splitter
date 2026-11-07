from decimal import Decimal

from django.db.models import Count, Max, Q, Sum
from django.db.models.functions import Coalesce
from django.shortcuts import render

from expenses.models import Expense, Status
from trips.models import Participant, Trip


def index(request):
    # Общие цифры по сервису: одной строкой aggregate() по расходам
    # и простым подсчетом поездок и участников. Отмененные расходы
    # в сумму не входят, их число показываем отдельно.
    summary = Expense.objects.aggregate(
        expenses_count=Count("pk", filter=Q(status=Status.ACTIVE)),
        expenses_total=Coalesce(
            Sum("amount", filter=Q(status=Status.ACTIVE)), Decimal("0")
        ),
        max_amount=Max("amount", filter=Q(status=Status.ACTIVE)),
        cancelled_count=Count("pk", filter=Q(status=Status.CANCELLED)),
    )
    summary["trips_count"] = Trip.objects.count()
    summary["participants_count"] = Participant.objects.count()
    return render(request, "homepage/index.html", {"summary": summary})
