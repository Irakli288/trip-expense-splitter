"""Тесты форм ПР11: фильтр, создание, редактирование, отмена, фото чека."""

import shutil
import tempfile
from datetime import date
from decimal import Decimal
from io import BytesIO

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from PIL import Image

from db.testing import ProjectDataMixin

from .forms import ExpenseFilterForm, ExpenseForm
from .models import Category, Expense, Status
from .validators import MAX_RECEIPT_SIZE_MB

# Загруженные в тестах файлы складываем во временную папку.
TEST_MEDIA = tempfile.mkdtemp()


def make_image(name="check.png", image_format="PNG"):
    """Маленькая настоящая картинка для загрузки."""
    buffer = BytesIO()
    Image.new("RGB", (20, 30), "white").save(buffer, image_format)
    return SimpleUploadedFile(
        name, buffer.getvalue(), content_type=f"image/{image_format.lower()}"
    )


def expense_data(**changes):
    """Данные формы нового расхода в поездке в Казань."""
    data = {
        "trip": 1,
        "title": "Такси до вокзала",
        "amount": "900",
        "category": Category.TRANSPORT,
        "expense_date": "2026-11-06",
        "payer": 3,
        "split_between": [1, 2, 3],
    }
    data.update(changes)
    return data


class ExpenseFilterFormTests(ProjectDataMixin, TestCase):
    def test_unbound_form(self):
        form = ExpenseFilterForm()
        self.assertFalse(form.is_bound)

    def test_valid_values_are_converted(self):
        form = ExpenseFilterForm({
            "q": "  анна ", "trip": "1", "min_amount": "5000",
            "category": "транспорт", "sort": "",
        })
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["q"], "анна")
        self.assertEqual(form.cleaned_data["trip"].name, "Поездка в Казань")
        self.assertEqual(form.cleaned_data["min_amount"], Decimal("5000"))
        self.assertEqual(form.cleaned_data["sort"], "date")

    def test_bad_values(self):
        form = ExpenseFilterForm({
            "trip": "999", "category": "казино", "status": "deleted",
            "min_amount": "-5", "sort": "password",
        })
        self.assertFalse(form.is_valid())
        self.assertEqual(
            set(form.errors),
            {"trip", "category", "status", "min_amount", "sort"},
        )

    def test_list_shows_form_and_errors(self):
        response = self.client.get("/expenses/", {"min_amount": "abc"})
        self.assertIsInstance(response.context["form"], ExpenseFilterForm)
        self.assertContains(response, "Проверьте параметры фильтрации")
        self.assertContains(response, "is-invalid")
        # Неправильный фильтр не применяется: показаны все расходы.
        self.assertEqual(response.context["summary"]["expenses_count"], 6)

    def test_selected_values_stay_in_form(self):
        response = self.client.get(
            "/expenses/", {"trip": 1, "category": "еда", "sort": "-amount"}
        )
        self.assertContains(response, '<option value="1" selected>')
        self.assertContains(response, '<option value="еда" selected>')
        self.assertContains(response, '<option value="-amount" selected>')
        titles = [expense.title for expense in response.context["expenses"]]
        self.assertEqual(titles, ["Ужин в ресторане"])


class ExpenseCreateTests(ProjectDataMixin, TestCase):
    url = reverse("expenses:create")

    def test_get_shows_empty_form(self):
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, "expenses/expense_form.html")
        form = response.context["form"]
        self.assertIsInstance(form, ExpenseForm)
        self.assertFalse(form.is_bound)
        self.assertNotIn("status", form.fields)
        self.assertContains(response, "csrfmiddlewaretoken")
        self.assertContains(response, 'enctype="multipart/form-data"')

    def test_trip_from_address(self):
        response = self.client.get(self.url, {"trip": 2})
        form = response.context["form"]
        self.assertTrue(form.fields["trip"].disabled)
        # Выбрать можно только участников этой поездки.
        names = [person.name for person in form.fields["payer"].queryset]
        self.assertEqual(names, ["Давид", "Ираклий"])
        self.assertEqual(
            self.client.get(self.url, {"trip": 999}).status_code, 404
        )

    def test_create_expense(self):
        response = self.client.post(self.url, expense_data())
        expense = Expense.objects.get(title="Такси до вокзала")
        # Страницу после перенаправления открываем сами ниже,
        # чтобы увидеть на ней сообщение.
        self.assertRedirects(
            response, expense.get_absolute_url(),
            fetch_redirect_response=False,
        )
        self.assertEqual(expense.status, Status.ACTIVE)
        self.assertEqual(expense.split_between.count(), 3)
        self.assertEqual(expense.get_share(), 300)
        page = self.client.get(expense.get_absolute_url())
        self.assertContains(page, "Расход «Такси до вокзала» добавлен.")

    def test_create_from_trip_page(self):
        data = expense_data(
            trip=1, expense_date="2027-07-15", payer=5, split_between=[4, 5]
        )
        response = self.client.post(self.url + "?trip=2", data)
        self.assertEqual(response.status_code, 302)
        # Поле поездки отключено: из POST оно не берется.
        self.assertEqual(Expense.objects.get(title="Такси до вокзала")
                         .trip_id, 2)

    def test_errors_are_shown_and_nothing_saved(self):
        response = self.client.post(self.url, expense_data(
            title="123", amount="0", payer="", split_between=[],
        ))
        self.assertEqual(response.status_code, 200)
        form = response.context["form"]
        self.assertEqual(
            set(form.errors), {"title", "amount", "payer", "split_between"}
        )
        self.assertContains(response, "хотя бы одну букву")
        self.assertEqual(Expense.objects.count(), 6)
        # Введенные значения остаются в форме.
        self.assertContains(response, 'value="123"')

    def test_date_outside_trip(self):
        response = self.client.post(
            self.url, expense_data(expense_date="2026-11-10")
        )
        self.assertFormError(
            response.context["form"], "expense_date",
            "Поездка «Поездка в Казань» идет с 03.11.2026 по 06.11.2026, "
            "дата расхода должна попадать в эти дни.",
        )
        self.assertEqual(Expense.objects.count(), 6)

    def test_people_from_other_trip(self):
        response = self.client.post(
            self.url, expense_data(payer=4, split_between=[1, 5])
        )
        form = response.context["form"]
        self.assertIn("payer", form.errors)
        self.assertIn("Давид", form.errors["split_between"][0])
        self.assertEqual(Expense.objects.count(), 6)

    def test_duplicate_active_expense(self):
        # «Ужин в ресторане», 4 500 ₽, 04.11.2026 уже есть в поездке.
        data = expense_data(
            title="ужин в ресторане", amount="4500", expense_date="2026-11-04"
        )
        response = self.client.post(self.url, data)
        errors = response.context["form"].non_field_errors()
        self.assertIn("уже учтен", errors[0])
        self.assertContains(response, "alert-danger")
        self.assertEqual(Expense.objects.count(), 6)

    def test_cancelled_expense_does_not_block(self):
        Expense.objects.filter(pk=3).update(status=Status.CANCELLED)
        data = expense_data(
            title="Ужин в ресторане", amount="4500", expense_date="2026-11-04"
        )
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            Expense.objects.filter(title="Ужин в ресторане").count(), 2
        )

    def test_initial_date_is_today(self):
        form = ExpenseForm()
        self.assertEqual(
            form.fields["expense_date"].initial, date.today()
        )


class ExpenseUpdateTests(ProjectDataMixin, TestCase):
    def test_form_filled_with_current_values(self):
        response = self.client.get("/expenses/3/edit/")
        form = response.context["form"]
        self.assertEqual(form.instance.pk, 3)
        self.assertTrue(form.fields["trip"].disabled)
        self.assertContains(response, 'value="Ужин в ресторане"')
        self.assertContains(response, 'value="2026-11-04"')

    def test_save_without_changes_keeps_one_record(self):
        form = ExpenseForm(instance=Expense.objects.get(pk=3))
        data = {
            name: form[name].value() for name in form.fields
            if name not in ("trip", "receipt")
        }
        response = self.client.post("/expenses/3/edit/", data)
        self.assertRedirects(response, "/expenses/3/")
        # Расход не конфликтует сам с собой и не задваивается.
        self.assertEqual(Expense.objects.count(), 6)

    def test_change_values(self):
        response = self.client.post("/expenses/3/edit/", expense_data(
            title="Ужин в кафе", amount="5200", expense_date="2026-11-05",
            payer=2, split_between=[2, 3],
        ))
        self.assertRedirects(response, "/expenses/3/")
        expense = Expense.objects.get(pk=3)
        self.assertEqual(expense.title, "Ужин в кафе")
        self.assertEqual(expense.amount, Decimal("5200"))
        self.assertEqual(expense.payer.name, "Анна")
        self.assertEqual(expense.split_between.count(), 2)
        self.assertEqual(Expense.objects.count(), 6)

    def test_trip_cannot_be_changed(self):
        self.client.post("/expenses/3/edit/", expense_data(trip=2))
        self.assertEqual(Expense.objects.get(pk=3).trip_id, 1)

    def test_conflict_with_other_expense(self):
        # Делаем ужин копией экскурсии (pk=4): 3 000 ₽, 05.11.2026.
        response = self.client.post("/expenses/3/edit/", expense_data(
            title="Экскурсия в Кремль", amount="3000",
            expense_date="2026-11-05",
        ))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["form"].non_field_errors())
        # В заголовке прежнее название, а не введенное.
        self.assertContains(response, "Изменить расход «Ужин в ресторане»")
        self.assertEqual(Expense.objects.get(pk=3).title, "Ужин в ресторане")

    def test_bad_date_on_edit(self):
        response = self.client.post(
            "/expenses/3/edit/", expense_data(expense_date="2026-10-01")
        )
        self.assertIn("expense_date", response.context["form"].errors)

    def test_missing_expense(self):
        self.assertEqual(self.client.get("/expenses/999/edit/").status_code,
                         404)


class ExpenseCancelTests(ProjectDataMixin, TestCase):
    def test_cancel_changes_status(self):
        response = self.client.post("/expenses/3/cancel/")
        self.assertRedirects(
            response, "/expenses/3/", fetch_redirect_response=False
        )
        expense = Expense.objects.get(pk=3)
        # Запись не удалена, у нее только новый статус.
        self.assertEqual(expense.status, Status.CANCELLED)
        self.assertEqual(Expense.objects.count(), 6)
        page = self.client.get("/expenses/3/")
        self.assertContains(page, "отменен и больше не входит в расчет")
        self.assertNotContains(page, reverse("expenses:cancel", args=[3]))

    def test_get_is_not_allowed(self):
        response = self.client.get("/expenses/3/cancel/")
        self.assertEqual(response.status_code, 405)
        self.assertEqual(Expense.objects.get(pk=3).status, Status.ACTIVE)

    def test_cancel_twice_or_missing(self):
        self.client.post("/expenses/3/cancel/")
        self.assertEqual(
            self.client.post("/expenses/3/cancel/").status_code, 404
        )
        self.assertEqual(
            self.client.post("/expenses/999/cancel/").status_code, 404
        )

    def test_cancelled_not_in_active_list(self):
        self.client.post("/expenses/3/cancel/")
        response = self.client.get("/expenses/", {"status": "active"})
        titles = [expense.title for expense in response.context["expenses"]]
        self.assertNotIn("Ужин в ресторане", titles)

    def test_buttons_in_list(self):
        response = self.client.get("/expenses/")
        self.assertContains(response, 'href="/expenses/1/edit/"')
        self.assertContains(response, 'action="/expenses/1/cancel/"')


class CsrfTests(ProjectDataMixin, TestCase):
    """Без CSRF-токена POST-запросы отклоняются (403)."""

    def setUp(self):
        self.client = Client(enforce_csrf_checks=True)

    def test_post_without_token(self):
        urls = ["/expenses/create/", "/expenses/3/edit/",
                "/expenses/3/cancel/"]
        for url in urls:
            with self.subTest(url=url):
                response = self.client.post(url, expense_data())
                self.assertEqual(response.status_code, 403)
        self.assertEqual(Expense.objects.count(), 6)
        self.assertEqual(Expense.objects.get(pk=3).status, Status.ACTIVE)

    def test_post_with_token(self):
        page = self.client.get("/expenses/create/")
        token = page.context["csrf_token"]
        data = expense_data(csrfmiddlewaretoken=str(token))
        response = self.client.post("/expenses/create/", data)
        self.assertEqual(response.status_code, 302)


@override_settings(MEDIA_ROOT=TEST_MEDIA)
class ReceiptUploadTests(ProjectDataMixin, TestCase):
    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEST_MEDIA, ignore_errors=True)
        super().tearDownClass()

    def test_upload_and_show(self):
        data = expense_data(receipt=make_image())
        response = self.client.post("/expenses/create/", data)
        expense = Expense.objects.get(title="Такси до вокзала")
        self.assertRedirects(response, expense.get_absolute_url())
        self.assertTrue(expense.receipt.name.startswith("receipts/"))
        page = self.client.get(expense.get_absolute_url())
        self.assertContains(page, f'src="{expense.receipt.url}"')

    def test_replace_on_edit(self):
        form = ExpenseForm(instance=Expense.objects.get(pk=3))
        data = {
            name: form[name].value() for name in form.fields
            if name not in ("trip", "receipt")
        }
        data["receipt"] = make_image("dinner.jpg", "JPEG")
        self.client.post("/expenses/3/edit/", data)
        self.assertIn("dinner", Expense.objects.get(pk=3).receipt.name)

    def test_without_receipt(self):
        page = self.client.get("/expenses/1/")
        self.assertContains(page, "чек не приложен")

    def test_not_an_image(self):
        fake = SimpleUploadedFile(
            "check.png", b"not an image", content_type="image/png"
        )
        response = self.client.post(
            "/expenses/create/", expense_data(receipt=fake)
        )
        self.assertIn("receipt", response.context["form"].errors)
        self.assertEqual(Expense.objects.count(), 6)

    def test_wrong_extension(self):
        response = self.client.post(
            "/expenses/create/",
            expense_data(receipt=make_image("check.gif", "GIF")),
        )
        self.assertIn("receipt", response.context["form"].errors)

    def test_too_big(self):
        image = make_image()
        image.size = MAX_RECEIPT_SIZE_MB * 1024 * 1024 + 1
        form = ExpenseForm(expense_data(), {"receipt": image})
        self.assertFalse(form.is_valid())
        self.assertIn("5 МБ", form.errors["receipt"][0])
