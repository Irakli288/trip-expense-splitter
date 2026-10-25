from django.test import SimpleTestCase
from django.urls import reverse

from db.testing import TemporaryDatabaseMixin


class ExpensePagesTests(TemporaryDatabaseMixin, SimpleTestCase):
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

    def test_expenses_search(self):
        response = self.client.get(
            "/expenses/",
            {"trip": 1, "category": "транспорт", "min_amount": 5000},
        )
        titles = [row["title"] for row in response.context["expenses"]]
        self.assertEqual(titles, ["Билеты на поезд"])
        self.assertEqual(response.context["summary"]["expenses_total"], 18000)

    def test_expenses_search_ignores_bad_values(self):
        response = self.client.get(
            "/expenses/",
            {"trip": "abc", "category": "' OR 1=1 --", "min_amount": "-5"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["expenses"]), 6)

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
        categories = response.context["categories"]
        self.assertEqual(categories[0]["category"], "транспорт")
        self.assertEqual(categories[0]["total"], 26000)
        payers = response.context["payers"]
        self.assertEqual(payers[-1]["participant_name"], "Давид")
        self.assertEqual(payers[-1]["paid_total"], 0)
        alerts = [row["name"] for row in response.context["budget_alerts"]]
        self.assertEqual(alerts, ["Поездка в Казань"])

    def test_statistics_having_parameter(self):
        response = self.client.get(
            "/expenses/statistics/", {"min_total": 20000}
        )
        categories = [
            row["category"] for row in response.context["big_categories"]
        ]
        self.assertEqual(categories, ["транспорт", "жилье"])
