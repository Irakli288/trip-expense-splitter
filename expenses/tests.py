from django.test import SimpleTestCase


class ExpensePagesTests(SimpleTestCase):
    def test_expenses_list(self):
        response = self.client.get("/expenses/")
        self.assertContains(response, "Билеты на поезд")

    def test_expense_detail(self):
        response = self.client.get("/expenses/1/")
        self.assertContains(response, "Поездка в Казань")
        self.assertContains(response, "Ираклий, Анна, Максим")

    def test_missing_expense(self):
        response = self.client.get("/expenses/999/")
        self.assertContains(
            response, "Расход не найден", status_code=404
        )
