"""Модели поездки и участника поездки.

Раньше (ПР7) поездки и участники лежали в таблицах trips и participants,
и страницы доставали их SQL-запросами. Теперь их описывают классы Django,
а таблицы создают миграции.
"""

from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Count, F, OuterRef, Q, Subquery, Sum
from django.db.models.functions import Coalesce
from django.urls import reverse

from expenses.choices import Status

from .slugs import unique_slug

# С какой доли потраченного бюджета показываем предупреждение.
BUDGET_WARNING_SHARE = Decimal("0.8")

# В итоги поездки входят только расходы, которые не отменены.
ACTIVE_EXPENSES = Q(expenses__status=Status.ACTIVE)


class TripQuerySet(models.QuerySet):
    """Готовые выборки поездок, которые нужны сразу нескольким страницам."""

    def with_totals(self):
        """Добавляет к каждой поездке итоги по расходам и участникам.

        total — сколько всего потрачено, expenses_count — сколько расходов,
        participants_count — сколько участников. Участников считаем
        отдельным подзапросом: если присоединить к поездке и расходы,
        и участников сразу, сумма расходов умножится на число участников.
        Отмененные расходы в сумму и количество не входят.
        """
        participants_count = (
            Participant.objects
            .filter(trip=OuterRef("pk"))
            .order_by()
            .values("trip")
            .annotate(count=Count("pk"))
            .values("count")
        )
        return self.annotate(
            total=Coalesce(
                Sum("expenses__amount", filter=ACTIVE_EXPENSES),
                Decimal("0"),
            ),
            expenses_count=Count("expenses", filter=ACTIVE_EXPENSES),
            participants_count=Coalesce(Subquery(participants_count), 0),
        )


class Trip(models.Model):
    """Совместная поездка: название, даты и бюджет."""

    name = models.CharField("название", max_length=200)
    # Часть адреса страницы: /trips/poezdka-v-kazan/. Если оставить
    # пустым, заполнится само по названию при сохранении.
    slug = models.SlugField(
        "адрес",
        max_length=200,
        unique=True,
        blank=True,
        help_text="Латиница, цифры и дефис. Пусто — возьмется из названия.",
    )
    start_date = models.DateField("дата начала")
    end_date = models.DateField("дата окончания")
    # Бюджет можно не задавать, тогда в поле будет NULL.
    budget = models.DecimalField(
        "бюджет, ₽",
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Можно не заполнять.",
    )

    objects = TripQuerySet.as_manager()

    class Meta:
        ordering = ["start_date", "pk"]
        verbose_name = "поездка"
        verbose_name_plural = "поездки"
        constraints = [
            # Поездка не может закончиться раньше, чем началась.
            models.CheckConstraint(
                condition=Q(start_date__lte=F("end_date")),
                name="trip_dates_in_order",
            ),
        ]

    def __str__(self):
        return self.name

    def clean(self):
        super().clean()
        # Адрес из одних цифр спутался бы со старым адресом /trips/<номер>/.
        if self.slug and self.slug.isdigit():
            raise ValidationError(
                {"slug": "Адрес не может состоять только из цифр."}
            )

    def save(self, *args, **kwargs):
        if not self.slug:
            others = Trip.objects.exclude(pk=self.pk)
            self.slug = unique_slug(others, self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("trips:detail", kwargs={"slug": self.slug})

    @property
    def duration(self):
        """Сколько дней длится поездка, считая первый и последний день."""
        return (self.end_date - self.start_date).days + 1

    def get_total(self):
        """Сколько потрачено в поездке.

        Если поездку взяли через with_totals(), сумма уже посчитана
        в том же запросе. Иначе считаем ее отдельным запросом.
        Отмененные расходы не считаются.
        """
        total = getattr(self, "total", None)
        if total is None:
            active = self.expenses.filter(status=Status.ACTIVE)
            total = active.aggregate(
                total=Coalesce(Sum("amount"), Decimal("0"))
            )["total"]
        return total

    @property
    def budget_level(self):
        """Насколько потрачен бюджет: none, ok, warning или over.

        По этому значению шаблон выбирает цвет отметки бюджета.
        Правило то же, что у метода Trip.budget_level() из ПР3.
        """
        total = self.get_total()
        if not self.budget:
            return "none"
        if total > self.budget:
            return "over"
        if total >= self.budget * BUDGET_WARNING_SHARE:
            return "warning"
        return "ok"

    @property
    def used_percent(self):
        """Сколько процентов бюджета уже потрачено (целое число)."""
        if not self.budget:
            return None
        return int(self.get_total() * 100 / self.budget)

    @property
    def budget_diff(self):
        """Сколько осталось до конца бюджета или на сколько он превышен."""
        if not self.budget:
            return None
        return abs(self.budget - self.get_total())


class Participant(models.Model):
    """Участник поездки. Один человек — одна запись на каждую поездку."""

    # Удалили поездку — удаляются и ее участники.
    trip = models.ForeignKey(
        Trip,
        on_delete=models.CASCADE,
        related_name="participants",
        verbose_name="поездка",
    )
    name = models.CharField(
        "имя",
        max_length=100,
        help_text="В одной поездке имена не повторяются.",
    )

    class Meta:
        ordering = ["name", "pk"]
        verbose_name = "участник"
        verbose_name_plural = "участники"
        constraints = [
            # В одной поездке не бывает двух участников с одинаковым именем.
            models.UniqueConstraint(
                fields=["trip", "name"],
                name="unique_participant_name_in_trip",
            ),
        ]

    def __str__(self):
        return f"{self.name} ({self.trip.name})"
