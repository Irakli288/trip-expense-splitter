import tempfile
from datetime import date
from decimal import Decimal
from pathlib import Path

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models import RestrictedError
from django.test import TestCase
from django.urls import reverse

from db import import_json, import_sqlite_to_orm
from db.testing import ProjectDataMixin
from expenses.models import Expense, Status

from .models import Participant, Trip
from .slugs import make_slug


class TripModelTests(ProjectDataMixin, TestCase):
    def test_str_and_duration(self):
        trip = Trip.objects.get(pk=1)
        self.assertEqual(str(trip), "Поездка в Казань")
        self.assertEqual(trip.duration, 4)
        self.assertEqual(
            str(Participant.objects.get(pk=1)), "Ираклий (Поездка в Казань)"
        )

    def test_reverse_relations(self):
        trip = Trip.objects.get(pk=1)
        names = list(trip.participants.values_list("name", flat=True))
        self.assertEqual(names, ["Анна", "Ираклий", "Максим"])
        self.assertEqual(trip.expenses.count(), 4)
        anna = trip.participants.get(name="Анна")
        self.assertEqual(anna.paid_expenses.count(), 2)
        self.assertEqual(anna.shared_expenses.count(), 4)

    def test_with_totals(self):
        kazan, altai = Trip.objects.with_totals()
        self.assertEqual(kazan.total, 51000)
        self.assertEqual(kazan.participants_count, 3)
        self.assertEqual(kazan.expenses_count, 4)
        self.assertEqual(kazan.budget_level, "warning")
        self.assertEqual(kazan.used_percent, 85)
        self.assertEqual(altai.total, 20000)
        self.assertEqual(altai.budget_level, "ok")

    def test_budget_level_without_annotation(self):
        trip = Trip.objects.get(pk=1)
        self.assertEqual(trip.get_total(), 51000)
        trip.budget = None
        self.assertEqual(trip.budget_level, "none")
        trip.budget = Decimal("50000")
        self.assertEqual(trip.budget_level, "over")
        self.assertEqual(trip.budget_diff, 1000)

    def test_dates_constraint(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            Trip.objects.create(
                name="Ошибка",
                start_date=date(2026, 5, 2),
                end_date=date(2026, 5, 1),
            )

    def test_unique_participant_name(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            Participant.objects.create(trip_id=1, name="Анна")
        # В другой поездке такое имя допустимо.
        Participant.objects.create(trip_id=2, name="Анна")

    def test_crud(self):
        trip = Trip.objects.create(
            name="Выходные в Твери",
            start_date=date(2026, 12, 5),
            end_date=date(2026, 12, 6),
        )
        trip.budget = Decimal("15000")
        trip.save(update_fields=["budget"])
        self.assertEqual(Trip.objects.get(name__startswith="Выходные").budget,
                         15000)
        trip.delete()
        self.assertFalse(Trip.objects.filter(pk=trip.pk).exists())

    def test_delete_rules(self):
        payer = Participant.objects.get(pk=1)
        with self.assertRaises(RestrictedError):
            payer.delete()
        # Поездка удаляется вместе с участниками и расходами.
        Trip.objects.get(pk=2).delete()
        self.assertEqual(Participant.objects.filter(trip_id=2).count(), 0)
        self.assertEqual(Expense.objects.filter(trip_id=2).count(), 0)

    def test_slug_from_name(self):
        self.assertEqual(Trip.objects.get(pk=1).slug, "poezdka-v-kazan")
        self.assertEqual(Trip.objects.get(pk=2).slug, "pokhod-na-altai")
        self.assertEqual(
            make_slug("Щучье озеро, 2026!"), "shchuche-ozero-2026"
        )
        self.assertEqual(make_slug("2025"), "trip-2025")
        self.assertEqual(make_slug("???"), "trip")

    def test_slug_is_unique(self):
        trip = Trip.objects.create(
            name="Поездка в Казань",
            start_date=date(2027, 1, 3),
            end_date=date(2027, 1, 5),
        )
        self.assertEqual(trip.slug, "poezdka-v-kazan-2")
        self.assertEqual(trip.get_absolute_url(), "/trips/poezdka-v-kazan-2/")
        # Переименование не меняет адрес: старые ссылки продолжают работать.
        trip.name = "Казань зимой"
        trip.save()
        self.assertEqual(trip.slug, "poezdka-v-kazan-2")

    def test_slug_only_digits(self):
        trip = Trip.objects.get(pk=1)
        trip.slug = "2026"
        with self.assertRaises(ValidationError):
            trip.full_clean()

    def test_cancelled_expense_not_in_totals(self):
        Expense.objects.filter(pk=1).update(status=Status.CANCELLED)
        kazan = Trip.objects.with_totals().get(pk=1)
        self.assertEqual(kazan.total, 25500)
        self.assertEqual(kazan.expenses_count, 3)
        self.assertEqual(Trip.objects.get(pk=1).get_total(), 25500)
        self.assertEqual(kazan.budget_level, "ok")


class TransferTests(TestCase):
    def test_transfer_keeps_ids_and_links(self):
        with tempfile.TemporaryDirectory() as folder:
            source_db = Path(folder) / "source.sqlite"
            import_json.main(source_db)
            counts = import_sqlite_to_orm.transfer(source_db)
            # Повторный запуск не создает дублей.
            self.assertEqual(import_sqlite_to_orm.transfer(source_db), counts)
        self.assertEqual(
            counts, {"trips": 2, "participants": 5, "expenses": 6}
        )
        expense = Expense.objects.select_related("trip", "payer").get(pk=4)
        self.assertEqual(expense.trip.name, "Поездка в Казань")
        self.assertEqual(expense.payer.name, "Анна")
        self.assertEqual(expense.expense_date, date(2026, 11, 5))
        self.assertEqual(
            list(expense.split_between.values_list("pk", flat=True)), [2, 3]
        )
        self.assertEqual(Trip.objects.get(pk=1).budget, 60000)

    def test_missing_source(self):
        with self.assertRaises(FileNotFoundError):
            import_sqlite_to_orm.transfer("no-such-file.sqlite")


class TripPagesTests(ProjectDataMixin, TestCase):
    def test_named_urls(self):
        self.assertEqual(reverse("trips:list"), "/trips/")
        self.assertEqual(
            reverse("trips:detail", args=["poezdka-v-kazan"]),
            "/trips/poezdka-v-kazan/",
        )
        self.assertEqual(
            reverse("trips:settlement", args=["poezdka-v-kazan"]),
            "/trips/poezdka-v-kazan/settlement/",
        )
        self.assertEqual(reverse("trips:by_id", args=[1]), "/trips/1/")

    def test_trips_list(self):
        response = self.client.get("/trips/")
        self.assertTemplateUsed(response, "trips/trip_list.html")
        self.assertTemplateUsed(response, "trips/includes/trip_card.html")
        self.assertContains(response, "Поездка в Казань")
        self.assertContains(response, "03.11.2026 – 06.11.2026")
        self.assertContains(response, "Всего поездок: 2")
        self.assertEqual(len(response.context["trips"]), 2)

    def test_trips_search(self):
        response = self.client.get("/trips/", {"q": "алтай"})
        names = [trip.name for trip in response.context["trips"]]
        self.assertEqual(names, ["Поход на Алтай"])
        response = self.client.get("/trips/", {"q": "Сочи"})
        self.assertContains(response, "Поездки не найдены.")

    def test_trip_detail(self):
        response = self.client.get("/trips/poezdka-v-kazan/")
        self.assertTemplateUsed(response, "trips/trip_detail.html")
        self.assertTemplateUsed(response, "trips/includes/budget_badge.html")
        self.assertContains(response, "Аренда квартиры")
        self.assertContains(response, "Максим")
        self.assertContains(response, "03.11.2026")
        self.assertContains(response, "израсходовано 85% бюджета")
        self.assertContains(
            response, 'href="/trips/poezdka-v-kazan/settlement/"'
        )

    def test_trip_detail_not_paid(self):
        response = self.client.get("/trips/pokhod-na-altai/")
        names = [person.name for person in response.context["not_paid"]]
        self.assertEqual(names, ["Давид"])

    def test_not_paid_ignores_cancelled(self):
        # Отменяем оба расхода Анны: она попадает в список неплативших.
        Expense.objects.filter(trip_id=1, payer__name="Анна").update(
            status=Status.CANCELLED
        )
        response = self.client.get("/trips/poezdka-v-kazan/")
        names = [person.name for person in response.context["not_paid"]]
        self.assertEqual(names, ["Анна"])
        self.assertContains(response, "Отменен")

    def test_old_address_redirects(self):
        response = self.client.get("/trips/1/")
        self.assertRedirects(
            response, "/trips/poezdka-v-kazan/", status_code=301
        )

    def test_trip_settlement(self):
        response = self.client.get("/trips/poezdka-v-kazan/settlement/")
        self.assertTemplateUsed(response, "trips/trip_settlement.html")
        self.assertContains(response, "Максим → Ираклий")
        self.assertContains(response, "Максим → Анна")

    def test_settlement_without_cancelled(self):
        # Отменяем все расходы поездки: переводить никому ничего не нужно.
        Expense.objects.filter(trip_id=1).update(status=Status.CANCELLED)
        response = self.client.get("/trips/poezdka-v-kazan/settlement/")
        self.assertContains(response, "Переводы не нужны")

    def test_missing_trip(self):
        response = self.client.get("/trips/999/")
        self.assertTemplateUsed(response, "trips/trip_detail.html")
        self.assertContains(
            response, "Поездка не найдена", status_code=404
        )

    def test_missing_trip_settlement(self):
        response = self.client.get("/trips/net-takoi/settlement/")
        self.assertContains(
            response, "Поездка не найдена", status_code=404
        )

    def test_missing_slug(self):
        response = self.client.get("/trips/net-takoi/")
        self.assertContains(
            response, "Поездка не найдена", status_code=404
        )

    def test_query_counts(self):
        """Число запросов страницы не растет вместе с числом записей.

        Один из запросов на каждой странице — число поездок для меню.
        """
        pages = {
            "/trips/": 2,
            "/trips/poezdka-v-kazan/": 5,
            "/trips/poezdka-v-kazan/settlement/": 5,
        }
        for url, count in pages.items():
            with self.subTest(url=url), self.assertNumQueries(count):
                self.client.get(url)

    def test_context_processor(self):
        response = self.client.get("/trips/")
        self.assertEqual(response.context["site_name"],
                         "Сервис расходов поездки")
        self.assertContains(response, 'text-primary">2</span>')
