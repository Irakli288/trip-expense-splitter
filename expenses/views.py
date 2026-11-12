import math
from decimal import Decimal

from django.core.paginator import Paginator
from django.db.models import Avg, Count, F, Max, Q, Sum
from django.db.models.functions import Coalesce
from django.shortcuts import render

from trips.models import BUDGET_WARNING_SHARE, Participant, Trip

from .forms import DEFAULT_SORT, SORT_OPTIONS, ExpenseFilterForm
from .models import Expense, Status

DEFAULT_MIN_TOTAL = 5000
EXPENSES_PER_PAGE = 5


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
    # Форма проверяет параметры из адреса. Без параметров форма
    # не связана с данными (is_bound = False): это первое открытие.
    form = ExpenseFilterForm(request.GET or None)
    form_valid = form.is_bound and form.is_valid()
    filters = form.cleaned_data if form_valid else {}
    trip = filters.get("trip")
    category = filters.get("category")
    status = filters.get("status")
    min_amount = filters.get("min_amount")
    query = filters.get("q")
    sort = filters.get("sort") or DEFAULT_SORT

    # Поездку и плательщика берем тем же запросом, что и расходы.
    found = Expense.objects.with_relations()
    # Фильтры применяются только после успешной проверки формы.
    if trip:
        found = found.for_trip(trip.pk)
    if status:
        found = found.filter(status=status)
    if category:
        found = found.filter(category=category)
    if min_amount:
        found = found.filter(amount__gte=min_amount)
    if query:
        # Ищем в названии расхода, имени плательщика и названии поездки.
        found = found.search(query)
    found = found.order_by(*SORT_OPTIONS[sort][1])

    # В итог входят только действующие расходы из найденных.
    summary = found.aggregate(
        expenses_count=Count("pk"),
        cancelled_count=Count("pk", filter=Q(status=Status.CANCELLED)),
        expenses_total=Coalesce(
            Sum("amount", filter=Q(status=Status.ACTIVE)), Decimal("0")
        ),
    )
    # Неправильный номер страницы (?page=abc или ?page=100)
    # заменяется ближайшей существующей страницей. Номер страницы
    # не входит в форму: это не условие отбора, а часть пагинации.
    page_obj = Paginator(found, EXPENSES_PER_PAGE).get_page(
        request.GET.get("page")
    )
    context = {
        "form": form,
        # Форма заполнена, но с ошибками: показываем предупреждение.
        "filter_error": form.is_bound and not form_valid,
        "expenses": page_obj.object_list,
        "page_obj": page_obj,
        "summary": summary,
    }
    return render(request, "expenses/expense_list.html", context)


def expense_detail(request, expense_id):
    try:
        expense = Expense.objects.with_relations().get(pk=expense_id)
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
    # Статистика считается только по действующим расходам.
    active = Expense.objects.active()
    paid_active = Q(paid_expenses__status=Status.ACTIVE)
    # values("category") + annotate() — это GROUP BY category.
    by_category = active.values("category").order_by()
    # Сколько расходов и на какую сумму в каждом статусе.
    by_status = (
        Expense.objects.values("status")
        .order_by("status")
        .annotate(expenses_count=Count("pk"), total=Sum("amount"))
    )
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
            expenses_count=Count("paid_expenses", filter=paid_active),
            paid_total=Coalesce(
                Sum("paid_expenses__amount", filter=paid_active),
                Decimal("0"),
            ),
        ).order_by("-paid_total", "name"),
        # Фильтр по уже посчитанной сумме — в SQL это HAVING.
        "big_categories": by_category.annotate(
            total=Sum("amount"),
        ).filter(total__gte=min_total).order_by("-total"),
        "budget_alerts": Trip.objects.with_totals()
        .exclude(budget__isnull=True)
        .filter(total__gte=F("budget") * BUDGET_WARNING_SHARE)
        .order_by((F("total") / F("budget")).desc()),
        "top_expenses": active.select_related("trip")
        .order_by("-amount", "pk")[:3],
        "by_status": [
            dict(row, label=Status(row["status"]).label)
            for row in by_status
        ],
        # is_large считает сама база, поэтому по нему можно фильтровать.
        "large_count": active.filter(is_large=True).count(),
        "min_total": request.GET.get("min_total", DEFAULT_MIN_TOTAL),
    }
    return render(request, "expenses/statistics.html", context)
