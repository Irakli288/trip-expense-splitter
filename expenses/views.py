from django.shortcuts import render

from models.expenses import find_expense_by_id, get_total, sort_expenses
from storage import load_all


def expenses(request):
    _, _, expenses_list = load_all()
    context = {
        "expenses": sort_expenses(expenses_list, by="date"),
        "total": get_total(expenses_list),
    }
    return render(request, "expenses/expense_list.html", context)


def expense_detail(request, expense_id):
    _, _, expenses_list = load_all()
    expense = find_expense_by_id(expenses_list, expense_id)
    context = {
        "expense": expense,
    }
    return render(
        request,
        "expenses/expense_detail.html",
        context,
        status=404 if expense is None else 200,
    )
