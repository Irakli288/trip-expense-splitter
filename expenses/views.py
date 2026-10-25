from django.http import HttpResponse


def expenses(request):
    return HttpResponse("Список расходов")


def expense_detail(request, expense_id):
    return HttpResponse(f"Расход {expense_id}")
