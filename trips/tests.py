from django.test import SimpleTestCase
from django.urls import reverse

from db.testing import TemporaryDatabaseMixin


class TripPagesTests(TemporaryDatabaseMixin, SimpleTestCase):
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
        self.assertContains(response, "Всего поездок: 2")
        self.assertEqual(len(response.context["trips"]), 2)

    def test_trips_list_totals_from_sqlite(self):
        response = self.client.get("/trips/")
        kazan = response.context["trips"][0]
        self.assertEqual(kazan["name"], "Поездка в Казань")
        self.assertEqual(kazan["total"], 51000)
        self.assertEqual(kazan["participants_count"], 3)
        self.assertEqual(kazan["duration"], 4)
        self.assertEqual(kazan["budget_level"], "warning")

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
        names = [row["name"] for row in response.context["not_paid"]]
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
