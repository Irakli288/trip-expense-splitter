from django.test import SimpleTestCase, override_settings

from db.testing import TemporaryDatabaseMixin


class HomepageTests(TemporaryDatabaseMixin, SimpleTestCase):
    def test_index(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "homepage/index.html")
        self.assertTemplateUsed(response, "base.html")
        self.assertTemplateUsed(response, "includes/navigation.html")
        self.assertContains(response, "bootstrap.min.css")
        self.assertContains(response, 'href="/trips/"')
        self.assertContains(response, 'href="/expenses/statistics/"')

    def test_summary_from_sqlite(self):
        response = self.client.get("/")
        summary = response.context["summary"]
        self.assertEqual(summary["trips_count"], 2)
        self.assertEqual(summary["participants_count"], 5)
        self.assertEqual(summary["expenses_count"], 6)
        self.assertEqual(summary["expenses_total"], 71000)

    def test_static_files(self):
        response = self.client.get("/")
        self.assertContains(response, "/static/homepage/css/style.css")
        self.assertContains(response, "/static/homepage/img/logo.png")
        self.assertContains(response, "/static/homepage/js/main.js")
        self.assertContains(response, 'id="current-year"')

    @override_settings(DEBUG=False)
    def test_custom_404(self):
        response = self.client.get("/nonexistent/")
        self.assertEqual(response.status_code, 404)
        self.assertTemplateUsed(response, "404.html")
        self.assertContains(
            response, "страница не найдена", status_code=404
        )
