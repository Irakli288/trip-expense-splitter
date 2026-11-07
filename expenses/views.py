import math
from decimal import Decimal

from django.core.paginator import Paginator
from django.db.models import Avg, Count, F, Max, Sum
from django.db.models.functions import Coalesce
from django.shortcuts import render

from splitter.search import text_search
from trips.models import BUDGET_WARNING_SHARE, Participant, Trip

from .models import Category, Expense

DEFAULT_MIN_TOTAL = 5000
EXPENSES_PER_PAGE = 5

# Какие сортировки можно выбрать в списке расходов. В order_by()
# попадают только поля из этого словаря, а не то, что пришло в адресе.
SORT_OPTIONS = {
    "date": ("сначала ранние", ["expense_date", "pk"]),
    "-date": ("сначала поздние", ["-expense_date", "-pk"]),
    "amount": ("сначала дешевые", ["amount", "pk"]),
    "-amount": ("сначала дорогие", ["-amount", "pk"]),
    "title": ("по названию", ["title", "pk"]),
    "trip": ("по поездке", ["trip__name", "expense_date", "pk"]),
}
DEFAULT_SORT = "date"


def parse_number(text, default=0, number_type=float):
    """Превращает параметр из адреса в неотрицательное число.

    Если значение пустое или кривое, берется значение по умолчанию.
    Так опечатка в адресе не ломает страницу.
    """
    try:
        value = number_type(text)
    except (TypeError, ValueError, ArithmeticError):
        return default
    # Отсекаем nan и бесконечность, а потом отрицательные числа.
    if not math.isfinite(value) or value < 0:
        return default
    return value


def expenses(request):
    trip_id = parse_number(request.GET.get("trip"), 0, int)
    category = request.GET.get("category", "")
    if category not in Category.values:
        category = ""
    min_amount = parse_number(request.GET.get("min_amount"), 0, Decimal)
    query = request.GET.get("q", "").strip()
    sort = request.GET.get("sort", DEFAULT_SORT)
    if sort not in SORT_OPTIONS:
        sort = DEFAULT_SORT

    # Поездку и плательщика берем тем же запросом, что и расходы.
    found = Expense.objects.select_related("trip", "payer")
    if trip_id:
        found = found.filter(trip_id=trip_id)
    if category:
        found = found.filter(category=category)
    if min_amount:
        found = found.filter(amount__gte=min_amount)
    if query:
        # Ищем в названии расхода, имени плательщика и названии поездки.
        found = found.filter(
            text_search(query, "title", "payer__name", "trip__name")
        )
    found = found.order_by(*SORT_OPTIONS[sort][1])

    summary = found.aggregate(
        expenses_count=Count("pk"),
        expenses_total=Coalesce(Sum("amount"), Decimal("0")),
    )
    # Неправильный номер страницы (?page=abc или ?page=100)
    # заменяется ближайшей существующей страницей.
    page_obj = Paginator(found, EXPENSES_PER_PAGE).get_page(
        request.GET.get("page")
    )
    context = {
        "expenses": page_obj.object_list,
        "page_obj": page_obj,
        "summary": summary,
        "trips": Trip.objects.only("name"),
        "categories": Category.values,
        "sort_options": {
            key: label for key, (label, _) in SORT_OPTIONS.items()
        },
        "selected_trip": trip_id,
        "selected_category": category,
        "selected_sort": sort,
        "query": query,
        "min_amount": request.GET.get("min_amount", ""),
    }
    return render(request, "expenses/expense_list.html", context)


def expense_detail(request, expense_id):
    try:
        expense = Expense.objects.select_related("trip", "payer").get(
            pk=expense_id
        )
    except Expense.DoesNotExist:
        expense = None
    shares = list(expense.split_between.order_by("pk")) if expense else []
    context = {
        "expense": expense,
        "shares": shares,
        "share": expense.get_share(len(shares)) if shares else 0,
    }
    return render(
        request,
        "expenses/expense_detail.html",
        context,
        status=404 if expense is None else 200,
    )


def statistics(request):
    min_total = parse_number(
        request.GET.get("min_total"), DEFAULT_MIN_TOTAL, Decimal
    )
    # values("category") + annotate() — это GROUP BY category.
    by_category = Expense.objects.values("category").order_by()
    context = {
        "categories": by_category.annotate(
            expenses_count=Count("pk"),
            total=Sum("amount"),
            average_amount=Avg("amount"),
            max_amount=Max("amount"),
        ).order_by("-total"),
        # Coalesce дает 0 тем, кто еще ни за что не платил:
        # такие участники тоже должны попасть в таблицу.
        "payers": Participant.objects.select_related("trip").annotate(
            expenses_count=Count("paid_expenses"),
            paid_total=Coalesce(Sum("paid_expenses__amount"), Decimal("0")),
        ).order_by("-paid_total", "name"),
        # Фильтр по уже посчитанной сумме — в SQL это HAVING.
        "big_categories": by_category.annotate(
            total=Sum("amount"),
        ).filter(total__gte=min_total).order_by("-total"),
        "budget_alerts": Trip.objects.with_totals()
        .exclude(budget__isnull=True)
        .filter(total__gte=F("budget") * BUDGET_WARNING_SHARE)
        .order_by((F("total") / F("budget")).desc()),
        "top_expenses": Expense.objects.select_related("trip")
        .order_by("-amount", "pk")[:3],
        "min_total": request.GET.get("min_total", DEFAULT_MIN_TOTAL),
    }
    return render(request, "expenses/statistics.html", context)
