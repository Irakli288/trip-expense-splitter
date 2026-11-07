import tempfile
from datetime import date
from decimal import Decimal
from pathlib import Path

from django.db import IntegrityError, transaction
from django.db.models import RestrictedError
from django.test import TestCase
from django.urls import reverse

from db import import_json, import_sqlite_to_orm
from db.testing import ProjectDataMixin
from expenses.models import Expense

from .models import Participant, Trip


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
        self.assertEqual(reverse("trips:detail", args=[1]), "/trips/1/")
        self.assertEqual(
            reverse("trips:settlement", args=[1]), "/trips/1/settlement/"
        )

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
        response = self.client.get("/trips/1/")
        self.assertTemplateUsed(response, "trips/trip_detail.html")
        self.assertTemplateUsed(response, "trips/includes/budget_badge.html")
        self.assertContains(response, "Аренда квартиры")
        self.assertContains(response, "Максим")
        self.assertContains(response, "03.11.2026")
        self.assertContains(response, "израсходовано 85% бюджета")
        self.assertContains(response, 'href="/trips/1/settlement/"')

    def test_trip_detail_not_paid(self):
        response = self.client.get("/trips/2/")
        names = [person.name for person in response.context["not_paid"]]
        self.assertEqual(names, ["Давид"])

    def test_trip_settlement(self):
        response = self.client.get("/trips/1/settlement/")
        self.assertTemplateUsed(response, "trips/trip_settlement.html")
        self.assertContains(response, "Максим → Ираклий")
        self.assertContains(response, "Максим → Анна")

    def test_missing_trip(self):
        response = self.client.get("/trips/999/")
        self.assertTemplateUsed(response, "trips/trip_detail.html")
        self.assertContains(
            response, "Поездка не найдена", status_code=404
        )

    def test_missing_trip_settlement(self):
        response = self.client.get("/trips/999/settlement/")
        self.assertContains(
            response, "Поездка не найдена", status_code=404
        )

    def test_not_int_id(self):
        response = self.client.get("/trips/abc/")
        self.assertEqual(response.status_code, 404)
