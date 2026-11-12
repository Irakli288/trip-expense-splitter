from datetime import date
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from db.testing import ProjectDataMixin
from models.expenses import CATEGORIES
from trips.models import Trip

from .models import Category, Expense, Status


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

    def test_status_by_default_active(self):
        expense = Expense.objects.get(pk=1)
        self.assertEqual(expense.status, Status.ACTIVE)
        self.assertFalse(expense.is_cancelled)
        self.assertEqual(expense.get_absolute_url(), "/expenses/1/")

    def test_unknown_status(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            Expense.objects.filter(pk=1).update(status="deleted")

    def test_manager_methods(self):
        Expense.objects.filter(pk=3).update(status=Status.CANCELLED)
        self.assertEqual(Expense.objects.active().count(), 5)
        self.assertEqual(
            list(Expense.objects.cancelled().values_list("pk", flat=True)),
            [3],
        )
        self.assertEqual(Expense.objects.for_trip(2).count(), 2)
        self.assertEqual(
            Expense.objects.active().for_trip(1).search("анна").count(), 2
        )
        # Методы менеджера доступны и через связь поездки.
        self.assertEqual(Expense.objects.get(pk=1).trip.expenses
                         .active().count(), 3)

    def test_is_large_counted_by_database(self):
        large = Expense.objects.filter(is_large=True)
        self.assertEqual(
            list(large.values_list("pk", flat=True)), [1, 2, 5]
        )
        expense = Expense.objects.get(pk=6)
        self.assertFalse(expense.is_large)
        expense.amount = Decimal("10000")
        expense.save()
        # Значение пересчитывает база, после сохранения его перечитывают.
        expense.refresh_from_db()
        self.assertTrue(expense.is_large)


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

    def test_status_filter_and_total(self):
        Expense.objects.filter(pk=1).update(status=Status.CANCELLED)
        response = self.client.get("/expenses/", {"trip": 1})
        summary = response.context["summary"]
        self.assertEqual(summary["expenses_count"], 4)
        self.assertEqual(summary["cancelled_count"], 1)
        # Отмененная аренда (25 500 ₽) в итог не входит.
        self.assertEqual(summary["expenses_total"], 25500)
        self.assertContains(response, "отменено: 1")
        response = self.client.get("/expenses/", {"status": "cancelled"})
        self.assertEqual(self.titles(response), ["Аренда квартиры"])
        # Неизвестный статус форма не пропускает: фильтр не применяется.
        response = self.client.get("/expenses/", {"status": "deleted"})
        self.assertTrue(response.context["filter_error"])
        self.assertEqual(response.context["summary"]["expenses_count"], 6)

    def test_cancelled_expense_detail(self):
        Expense.objects.filter(pk=1).update(status=Status.CANCELLED)
        response = self.client.get("/expenses/1/")
        self.assertContains(response, "не входит в итоги")

    def test_query_counts(self):
        """Запросов столько же при любом числе расходов на странице.

        Один из запросов — число поездок для меню.
        """
        pages = {
            "/expenses/": 5,
            "/expenses/1/": 3,
            "/expenses/statistics/": 8,
        }
        for url, count in pages.items():
            with self.subTest(url=url), self.assertNumQueries(count):
                self.client.get(url)

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
        self.assertEqual(response.context["large_count"], 3)

    def test_statistics_without_cancelled(self):
        Expense.objects.filter(pk=1).update(status=Status.CANCELLED)
        response = self.client.get("/expenses/statistics/")
        top = [expense.title for expense in response.context["top_expenses"]]
        self.assertNotIn("Аренда квартиры", top)
        categories = [
            row["category"] for row in response.context["categories"]
        ]
        self.assertNotIn("жилье", categories)
        by_status = {
            row["label"]: (row["expenses_count"], row["total"])
            for row in response.context["by_status"]
        }
        self.assertEqual(by_status["Отменен"], (1, 25500))
        self.assertEqual(by_status["Учитывается"], (5, 45500))

    def test_statistics_having_parameter(self):
        response = self.client.get(
            "/expenses/statistics/", {"min_total": 20000}
        )
        categories = [
            row["category"] for row in response.context["big_categories"]
        ]
        self.assertEqual(categories, ["транспорт", "жилье"])


class AdminTests(ProjectDataMixin, TestCase):
    """Страницы админки открываются, а действия и проверки работают."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.admin = User.objects.create_superuser(
            "admin", "admin@example.com", "admin-password"
        )

    def setUp(self):
        self.client.force_login(self.admin)

    def test_pages_open(self):
        pages = [
            "/admin/",
            "/admin/trips/trip/",
            "/admin/trips/trip/1/change/",
            "/admin/trips/trip/add/",
            "/admin/trips/participant/",
            "/admin/trips/participant/1/change/",
            "/admin/expenses/expense/",
            "/admin/expenses/expense/1/change/",
            "/admin/expenses/expense/add/",
            "/admin/expenses/expense/?q=анна",
            "/admin/expenses/expense/?status__exact=active&is_large__exact=1",
        ]
        for url in pages:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 200)

    def test_admin_headers(self):
        response = self.client.get("/admin/")
        self.assertContains(response, "Сервис расходов поездки")
        self.assertContains(response, "Поездки и участники")
        self.assertContains(response, "Расходы")

    def test_trip_list_columns(self):
        response = self.client.get("/admin/trips/trip/")
        self.assertContains(response, "51000")
        self.assertContains(response, 'href="/trips/poezdka-v-kazan/"')

    def test_list_queries_do_not_grow(self):
        """Поездка и плательщик берутся одним запросом со списком."""
        with self.assertNumQueries(8):
            self.client.get("/admin/expenses/expense/")
        for number in range(10):
            Expense.objects.create(
                trip_id=1, title=f"Такси {number}", amount=Decimal("300"),
                expense_date=date(2026, 11, 4), payer_id=2,
            )
        with self.assertNumQueries(8):
            self.client.get("/admin/expenses/expense/")

    def test_cancel_and_restore_actions(self):
        url = "/admin/expenses/expense/"
        self.client.post(url, {
            "action": "cancel_expenses", "_selected_action": [1, 2],
        })
        self.assertEqual(Expense.objects.cancelled().count(), 2)
        self.client.post(url, {
            "action": "restore_expenses", "_selected_action": [1],
        })
        self.assertEqual(
            list(Expense.objects.cancelled().values_list("pk", flat=True)),
            [2],
        )

    def test_form_checks_participants(self):
        response = self.client.post("/admin/expenses/expense/add/", {
            "trip": 1,
            "title": "Такси",
            "amount": "500",
            "category": Category.TRANSPORT,
            "expense_date": "2026-11-04",
            "payer": 4,
            "split_between": [1, 5],
            "status": Status.ACTIVE,
        })
        self.assertEqual(response.status_code, 200)
        form = response.context["adminform"].form
        self.assertIn("payer", form.errors)
        self.assertIn("split_between", form.errors)
        self.assertEqual(Expense.objects.count(), 6)

    def test_add_expense(self):
        response = self.client.post("/admin/expenses/expense/add/", {
            "trip": 1,
            "title": "Такси",
            "amount": "15000",
            "category": Category.TRANSPORT,
            "expense_date": "2026-11-04",
            "payer": 2,
            "split_between": [1, 2],
            "status": Status.ACTIVE,
        })
        self.assertEqual(response.status_code, 302)
        expense = Expense.objects.get(title="Такси")
        self.assertTrue(expense.is_large)
        self.assertEqual(expense.split_between.count(), 2)

    def test_add_trip_with_participants(self):
        response = self.client.post("/admin/trips/trip/add/", {
            "name": "Выходные в Твери",
            "slug": "",
            "start_date": "2026-12-05",
            "end_date": "2026-12-06",
            "budget": "",
            "participants-TOTAL_FORMS": "2",
            "participants-INITIAL_FORMS": "0",
            "participants-0-name": "Ираклий",
            "participants-1-name": "Анна",
            "expenses-TOTAL_FORMS": "0",
            "expenses-INITIAL_FORMS": "0",
        })
        self.assertEqual(response.status_code, 302)
        trip = Trip.objects.get(name="Выходные в Твери")
        self.assertEqual(trip.slug, "vykhodnye-v-tveri")
        self.assertEqual(trip.participants.count(), 2)
