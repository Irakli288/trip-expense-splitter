from django.test import SimpleTestCase


class TripPagesTests(SimpleTestCase):
    def test_trips_list(self):
        response = self.client.get("/trips/")
        self.assertContains(response, "Поездка в Казань")

    def test_trip_detail(self):
        response = self.client.get("/trips/1/")
        self.assertContains(response, "Аренда квартиры")
        self.assertContains(response, "Максим")

    def test_trip_settlement(self):
        response = self.client.get("/trips/1/settlement/")
        self.assertContains(response, "Максим → Ираклий")

    def test_missing_trip(self):
        response = self.client.get("/trips/999/")
        self.assertContains(
            response, "Поездка не найдена", status_code=404
        )

    def test_not_int_id(self):
        response = self.client.get("/trips/abc/")
        self.assertEqual(response.status_code, 404)
