from django.http import HttpResponse

from homepage.views import page
from models.expenses import find_expense_by_id, get_total, sort_expenses
from storage import load_all
from utils import format_money


def expenses(request):
    _, _, expenses_list = load_all()
    rows = ""
    for expense in sort_expenses(expenses_list, by="date"):
        rows += f"""
        <tr>
            <td>{expense.date:%d.%m.%Y}</td>
            <td><a href="/expenses/{expense.id}/">{expense.title}</a></td>
            <td>
                <a href="/trips/{expense.trip.id}/">{expense.trip.name}</a>
            </td>
            <td><span class="badge bg-info text-dark">
                {expense.category}
            </span></td>
            <td class="text-end">{format_money(expense.amount)}</td>
        </tr>
        """
    content = f"""
    <h1>Расходы</h1>
    <table class="table table-hover">
        <thead>
            <tr>
                <th>Дата</th>
                <th>Расход</th>
                <th>Поездка</th>
                <th>Категория</th>
                <th class="text-end">Сумма</th>
            </tr>
        </thead>
        <tbody>{rows}</tbody>
    </table>
    <p class="fw-bold">Итого: {format_money(get_total(expenses_list))}</p>
    """
    return HttpResponse(page("Расходы", content))


def expense_detail(request, expense_id):
    _, _, expenses_list = load_all()
    expense = find_expense_by_id(expenses_list, expense_id)
    if expense is None:
        content = """
        <h1 class="text-danger">Расход не найден</h1>
        <a href="/expenses/" class="btn btn-outline-secondary">
            ← к списку расходов
        </a>
        """
        return HttpResponse(page("Расход не найден", content), status=404)

    split = ", ".join(person.name for person in expense.split_between)
    content = f"""
    <div class="card">
        <div class="card-body">
            <h1 class="card-title h3">{expense.title}</h1>
            <p class="card-text">
                <strong>Поездка:</strong>
                <a href="/trips/{expense.trip.id}/">{expense.trip.name}</a>
            </p>
            <p class="card-text">
                <strong>Сумма:</strong> {format_money(expense.amount)}
                <span class="badge bg-info text-dark">
                    {expense.category}
                </span>
            </p>
            <p class="card-text">
                <strong>Дата:</strong> {expense.date:%d.%m.%Y}
            </p>
            <p class="card-text">
                <strong>Оплатил:</strong> {expense.payer.name}
            </p>
            <p class="card-text">
                <strong>Делится между:</strong> {split}
                (по {format_money(expense.share)} с каждого)
            </p>
            <a href="/expenses/" class="btn btn-outline-secondary">
                ← к списку расходов
            </a>
        </div>
    </div>
    """
    return HttpResponse(page(expense.title, content))
