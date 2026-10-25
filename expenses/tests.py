from django.test import SimpleTestCase
from django.urls import reverse


class ExpensePagesTests(SimpleTestCase):
    def test_named_urls(self):
        self.assertEqual(reverse("expenses:list"), "/expenses/")
        self.assertEqual(reverse("expenses:detail", args=[1]), "/expenses/1/")

    def test_expenses_list(self):
        response = self.client.get("/expenses/")
        self.assertTemplateUsed(response, "expenses/expense_list.html")
        self.assertTemplateUsed(
            response, "expenses/includes/category_badge.html"
        )
        self.assertContains(response, "Билеты на поезд")
        self.assertContains(response, "Всего расходов: 4")

    def test_expense_detail(self):
        response = self.client.get("/expenses/1/")
        self.assertTemplateUsed(response, "expenses/expense_detail.html")
        self.assertContains(response, "Поездка в Казань")
        self.assertContains(response, "Ираклий, Анна, Максим")

    def test_missing_expense(self):
        response = self.client.get("/expenses/999/")
        self.assertContains(
            response, "Расход не найден", status_code=404
        )
