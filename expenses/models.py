"""Модель расхода поездки.

Расход связан с поездкой и с участником, который за него заплатил
(связи «многие к одному»), а также с участниками, на которых он делится
(связь «многие ко многим»). Таблицу связи для split_between Django
создает сам: она заменяет таблицу expense_shares из ПР7.
"""

from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q

from models.expenses import calculate_share
from trips.models import Participant, Trip


class Category(models.TextChoices):
    """Категории расходов. Значения те же, что CATEGORIES из ПР3."""

    HOUSING = "жилье", "Жилье"
    TRANSPORT = "транспорт", "Транспорт"
    FOOD = "еда", "Еда"
    ENTERTAINMENT = "развлечения", "Развлечения"
    OTHER = "прочее", "Прочее"


class Expense(models.Model):
    """Трата в поездке: сколько, на что, кто заплатил и на кого делится."""

    # Удалили поездку — удаляются и ее расходы.
    trip = models.ForeignKey(
        Trip,
        on_delete=models.CASCADE,
        related_name="expenses",
        verbose_name="поездка",
    )
    title = models.CharField("название", max_length=200)
    amount = models.DecimalField(
        "сумма, ₽",
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
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
    )
    split_between = models.ManyToManyField(
        Participant,
        related_name="shared_expenses",
        verbose_name="делится между",
    )

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
        ]

    def __str__(self):
        return f"{self.title} — {self.amount} ₽"

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
