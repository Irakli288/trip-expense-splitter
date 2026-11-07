from datetime import date
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse

from db.testing import ProjectDataMixin
from models.expenses import CATEGORIES

from .models import Category, Expense


class ExpenseModelTests(ProjectDataMixin, TestCase):
    def test_categories_match_console_version(self):
        self.assertEqual(tuple(Category.values), CATEGORIES)

    def test_str_and_share(self):
        expense = Expense.objects.get(pk=1)
        self.assertEqual(str(expense), "Аренда квартиры — 25500.00 ₽")
        self.assertEqual(expense.get_share(), 8500)

    def test_amount_must_be_positive(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            Expense.objects.create(
                trip_id=1, title="Ошибка", amount=0,
                expense_date=date(2026, 11, 3), payer_id=1,
            )

    def test_unknown_category(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            Expense.objects.create(
                trip_id=1, title="Ошибка", amount=10, category="казино",
                expense_date=date(2026, 11, 3), payer_id=1,
            )

    def test_payer_from_other_trip(self):
        expense = Expense(
            trip_id=1, title="Такси", amount=Decimal("500"),
            expense_date=date(2026, 11, 3), payer_id=4,
        )
        with self.assertRaises(ValidationError):
            expense.full_clean()

    def test_create_with_split(self):
        expense = Expense.objects.create(
            trip_id=1, title="Такси", amount=Decimal("900"),
            category=Category.TRANSPORT,
            expense_date=date(2026, 11, 6), payer_id=3,
        )
        expense.split_between.set([1, 3])
        self.assertEqual(expense.get_share(), 450)
        self.assertEqual(
            Expense.objects.filter(split_between__name="Ираклий")
            .filter(trip_id=1).count(),
            4,
        )


class ExpensePagesTests(ProjectDataMixin, TestCase):
    def titles(self, response):
        return [expense.title for expense in response.context["expenses"]]

    def test_named_urls(self):
        self.assertEqual(reverse("expenses:list"), "/expenses/")
        self.assertEqual(reverse("expenses:detail", args=[1]), "/expenses/1/")
        self.assertEqual(
            reverse("expenses:statistics"), "/expenses/statistics/"
        )

    def test_expenses_list(self):
        response = self.client.get("/expenses/")
        self.assertTemplateUsed(response, "expenses/expense_list.html")
        self.assertTemplateUsed(
            response, "expenses/includes/category_badge.html"
        )
        self.assertContains(response, "Билеты на поезд")
        self.assertContains(response, "Найдено расходов: 6")
        self.assertContains(response, "03.11.2026")

    def test_expenses_filter(self):
        response = self.client.get(
            "/expenses/",
            {"trip": 1, "category": "транспорт", "min_amount": 5000},
        )
        self.assertEqual(self.titles(response), ["Билеты на поезд"])
        self.assertEqual(response.context["summary"]["expenses_total"], 18000)

    def test_expenses_search(self):
        response = self.client.get("/expenses/", {"q": "аренда"})
        self.assertEqual(
            self.titles(response), ["Аренда квартиры", "Аренда снаряжения"]
        )
        # Ищем и по имени плательщика, а не только по названию расхода.
        response = self.client.get("/expenses/", {"q": "Анна"})
        self.assertEqual(
            self.titles(response), ["Билеты на поезд", "Экскурсия в Кремль"]
        )
        response = self.client.get("/expenses/", {"q": "алтай"})
        self.assertEqual(response.context["summary"]["expenses_count"], 2)

    def test_expenses_sort(self):
        response = self.client.get("/expenses/", {"sort": "-amount"})
        self.assertEqual(
            self.titles(response)[:2], ["Аренда квартиры", "Билеты на поезд"]
        )
        response = self.client.get("/expenses/", {"sort": "trip"})
        self.assertEqual(self.titles(response)[0], "Аренда квартиры")
        self.assertEqual(
            response.context["expenses"][0].trip.name, "Поездка в Казань"
        )

    def test_pagination_keeps_parameters(self):
        response = self.client.get(
            "/expenses/", {"sort": "-amount", "page": 2}
        )
        self.assertEqual(self.titles(response), ["Экскурсия в Кремль"])
        self.assertContains(response, "страница 2 из 2")
        self.assertContains(response, 'href="?sort=-amount&amp;page=1"')

    def test_expenses_ignore_bad_values(self):
        response = self.client.get(
            "/expenses/",
            {
                "trip": "abc",
                "category": "' OR 1=1 --",
                "min_amount": "nan",
                "sort": "password",
                "page": "999",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["summary"]["expenses_count"], 6)
        self.assertEqual(response.context["page_obj"].number, 2)

    def test_expense_detail(self):
        response = self.client.get("/expenses/1/")
        self.assertTemplateUsed(response, "expenses/expense_detail.html")
        self.assertContains(response, "Поездка в Казань")
        self.assertContains(response, "Ираклий, Анна, Максим")
        self.assertContains(response, "по 8\xa0500,00 ₽ с каждого")

    def test_missing_expense(self):
        response = self.client.get("/expenses/999/")
        self.assertContains(
            response, "Расход не найден", status_code=404
        )

    def test_statistics(self):
        response = self.client.get("/expenses/statistics/")
        self.assertTemplateUsed(response, "expenses/statistics.html")
        categories = list(response.context["categories"])
        self.assertEqual(categories[0]["category"], "транспорт")
        self.assertEqual(categories[0]["total"], 26000)
        self.assertEqual(categories[0]["average_amount"], 13000)
        payers = list(response.context["payers"])
        self.assertEqual(payers[-1].name, "Давид")
        self.assertEqual(payers[-1].paid_total, 0)
        alerts = [trip.name for trip in response.context["budget_alerts"]]
        self.assertEqual(alerts, ["Поездка в Казань"])
        top = [expense.title for expense in response.context["top_expenses"]]
        self.assertEqual(
            top, ["Аренда квартиры", "Билеты на поезд", "Аренда снаряжения"]
        )

    def test_statistics_having_parameter(self):
        response = self.client.get(
            "/expenses/statistics/", {"min_total": 20000}
        )
        categories = [
            row["category"] for row in response.context["big_categories"]
        ]
        self.assertEqual(categories, ["транспорт", "жилье"])
