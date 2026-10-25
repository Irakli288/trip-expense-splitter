from django.urls import path

from . import views

app_name = "expenses"

urlpatterns = [
    path("", views.expenses, name="list"),
    path("statistics/", views.statistics, name="statistics"),
    path("<int:expense_id>/", views.expense_detail, name="detail"),
]
