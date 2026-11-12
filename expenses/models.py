"""Модель расхода поездки.

Расход связан с поездкой и с участником, который за него заплатил
(связи «многие к одному»), а также с участниками, на которых он делится
(связь «многие ко многим»). Таблицу связи для split_between Django
создает сам: она заменяет таблицу expense_shares из ПР7.
"""

from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator, MinValueValidator
from django.db import models
from django.db.models import Case, Q, Value, When
from django.urls import reverse

from models.expenses import calculate_share
from splitter.search import text_search
from trips.models import Participant, Trip

from .choices import Category, Status
from .validators import validate_receipt_size

# С какой суммы расход считается крупным (поле is_large).
LARGE_EXPENSE_AMOUNT = Decimal("10000")

__all__ = ["Category", "Expense", "ExpenseQuerySet", "Status"]


class ExpenseQuerySet(models.QuerySet):
    """Готовые выборки расходов, чтобы не повторять условия во views."""

    def active(self):
        """Только расходы, которые входят в итоги и расчет."""
        return self.filter(status=Status.ACTIVE)

    def cancelled(self):
        """Только отмененные расходы."""
        return self.filter(status=Status.CANCELLED)

    def for_trip(self, trip_id):
        """Расходы одной поездки."""
        return self.filter(trip_id=trip_id)

    def search(self, query):
        """Поиск по названию расхода, имени плательщика и поездке."""
        return self.filter(
            text_search(query, "title", "payer__name", "trip__name")
        )

    def with_relations(self):
        """Поездка и плательщик тем же запросом (без N+1 в списках)."""
        return self.select_related("trip", "payer")


class Expense(models.Model):
    """Трата в поездке: сколько, на что, кто заплатил и на кого делится."""

    # Удалили поездку — удаляются и ее расходы.
    trip = models.ForeignKey(
        Trip,
        on_delete=models.CASCADE,
        related_name="expenses",
        verbose_name="поездка",
    )
    title = models.CharField(
        "название",
        max_length=200,
        help_text="Например: «Билеты на поезд».",
    )
    amount = models.DecimalField(
        "сумма, ₽",
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
        help_text="Больше нуля, копейки через точку.",
    )
    category = models.CharField(
        "категория",
        max_length=20,
        choices=Category.choices,
        default=Category.OTHER,
    )
    expense_date = models.DateField("дата")
    # Участника, который за что-то платил, отдельно удалить нельзя:
    # иначе расход останется без плательщика и расчет сломается.
    # RESTRICT, в отличие от PROTECT, не мешает удалить всю поездку:
    # тогда участник и его расходы удаляются вместе.
    payer = models.ForeignKey(
        Participant,
        on_delete=models.RESTRICT,
        related_name="paid_expenses",
        verbose_name="оплатил",
        help_text="Участник этой же поездки.",
    )
    split_between = models.ManyToManyField(
        Participant,
        related_name="shared_expenses",
        verbose_name="делится между",
        help_text="Участники этой же поездки, на которых делится расход.",
    )
    status = models.CharField(
        "статус",
        max_length=10,
        choices=Status.choices,
        default=Status.ACTIVE,
        help_text="Отмененный расход не входит в итоги и расчет долгов.",
    )
    # Фото чека — необязательное. Сам файл лежит в папке media/receipts/,
    # а в базе хранится только путь к нему.
    receipt = models.ImageField(
        "фото чека",
        upload_to="receipts/%Y/%m/",
        blank=True,
        validators=[
            FileExtensionValidator(["jpg", "jpeg", "png", "webp"]),
            validate_receipt_size,
        ],
        help_text="JPG, PNG или WebP, не больше 5 МБ. Можно не прикладывать.",
    )
    # Признак считает сама база по сумме расхода, руками его не меняют.
    is_large = models.GeneratedField(
        expression=Case(
            When(amount__gte=LARGE_EXPENSE_AMOUNT, then=Value(True)),
            default=Value(False),
            output_field=models.BooleanField(),
        ),
        output_field=models.BooleanField(),
        db_persist=True,
        verbose_name="крупный расход",
    )

    objects = ExpenseQuerySet.as_manager()

    class Meta:
        ordering = ["expense_date", "pk"]
        verbose_name = "расход"
        verbose_name_plural = "расходы"
        constraints = [
            models.CheckConstraint(
                condition=Q(amount__gt=0),
                name="expense_amount_positive",
            ),
            models.CheckConstraint(
                condition=Q(category__in=Category.values),
                name="expense_category_known",
            ),
            models.CheckConstraint(
                condition=Q(status__in=Status.values),
                name="expense_status_known",
            ),
        ]

    def __str__(self):
        return f"{self.title} — {self.amount} ₽"

    def get_absolute_url(self):
        return reverse("expenses:detail", args=[self.pk])

    @property
    def is_cancelled(self):
        return self.status == Status.CANCELLED

    def cancel(self):
        """Отменяет расход: запись остается, но не входит в итоги."""
        self.status = Status.CANCELLED
        self.save(update_fields=["status"])

    def clean(self):
        """Платить за расход может только участник этой же поездки."""
        super().clean()
        if (
            self.trip_id
            and self.payer_id
            and self.payer.trip_id != self.trip_id
        ):
            raise ValidationError(
                {"payer": "Плательщик должен быть участником этой поездки."}
            )

    def get_share(self, people_count=None):
        """Доля одного участника, округленная вверх до копеек."""
        if people_count is None:
            people_count = self.split_between.count()
        return calculate_share(float(self.amount), people_count)
