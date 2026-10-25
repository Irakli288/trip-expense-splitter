from django.urls import path

from . import views

urlpatterns = [
    path("", views.expenses, name="expenses"),
    path("<int:expense_id>/", views.expense_detail, name="expense_detail"),
]
