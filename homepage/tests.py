from django.test import SimpleTestCase, override_settings


class HomepageTests(SimpleTestCase):
    def test_index(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "bootstrap.min.css")
        self.assertContains(response, 'href="/trips/"')

    @override_settings(DEBUG=False)
    def test_custom_404(self):
        response = self.client.get("/nonexistent/")
        self.assertEqual(response.status_code, 404)
        self.assertContains(
            response, "страница не найдена", status_code=404
        )
