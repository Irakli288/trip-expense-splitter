from django.test import SimpleTestCase
from django.urls import reverse


class TripPagesTests(SimpleTestCase):
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
        self.assertEqual(len(response.context["trip_rows"]), 2)

    def test_trip_detail(self):
        response = self.client.get("/trips/1/")
        self.assertTemplateUsed(response, "trips/trip_detail.html")
        self.assertTemplateUsed(response, "trips/includes/budget_badge.html")
        self.assertContains(response, "Аренда квартиры")
        self.assertContains(response, "Максим")
        self.assertContains(response, "03.11.2026")
        self.assertContains(response, 'href="/trips/1/settlement/"')

    def test_trip_settlement(self):
        response = self.client.get("/trips/1/settlement/")
        self.assertTemplateUsed(response, "trips/trip_settlement.html")
        self.assertContains(response, "Максим → Ираклий")

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
