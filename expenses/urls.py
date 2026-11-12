from django.urls import path

from . import views

app_name = "expenses"

urlpatterns = [
    path("", views.expenses, name="list"),
    path("statistics/", views.statistics, name="statistics"),
    # Постоянный адрес create/ стоит раньше адресов с номером расхода.
    path("create/", views.expense_create, name="create"),
    path("<int:expense_id>/", views.expense_detail, name="detail"),
    path("<int:expense_id>/edit/", views.expense_update, name="update"),
    path("<int:expense_id>/cancel/", views.expense_cancel, name="cancel"),
]
