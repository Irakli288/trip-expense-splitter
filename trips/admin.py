"""Админка поездок и участников."""

from django.contrib import admin
from django.db.models import Count
from django.urls import reverse
from django.utils.html import format_html

from expenses.models import Expense

from .models import Participant, Trip

admin.site.site_header = "Сервис расходов поездки"
admin.site.site_title = "Админка сервиса расходов"
admin.site.index_title = "Управление данными"


class ParticipantInline(admin.TabularInline):
    """Участники прямо на странице поездки."""

    model = Participant
    extra = 1
    fields = ["name"]


class TripExpenseInline(admin.TabularInline):
    """Расходы поездки только для просмотра.

    Добавлять расход удобнее на его собственной странице: там видны
    все поля и проверки. Отсюда к нему ведет ссылка.
    """

    model = Expense
    extra = 0
    fields = ["title", "amount", "category", "expense_date", "payer", "status"]
    readonly_fields = fields
    show_change_link = True
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False

    def get_queryset(self, request):
        # У плательщика в строке пишется и поездка: берем все сразу.
        return super().get_queryset(request).select_related("payer__trip")


@admin.register(Trip)
class TripAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "start_date",
        "end_date",
        "budget",
        "total_display",
        "participants_count",
        "site_link",
    ]
    list_display_links = ["name"]
    search_fields = ["name", "slug"]
    list_filter = ["start_date"]
    date_hierarchy = "start_date"
    ordering = ["-start_date", "pk"]
    list_per_page = 20
    # Адрес подставляется из названия прямо при вводе.
    prepopulated_fields = {"slug": ["name"]}
    fieldsets = [
        (None, {"fields": ["name", "slug"]}),
        ("Даты и бюджет", {"fields": [("start_date", "end_date"), "budget"]}),
    ]
    inlines = [ParticipantInline, TripExpenseInline]

    def get_queryset(self, request):
        # Итоги для столбцов списка считаются тем же запросом.
        return super().get_queryset(request).with_totals()

    @admin.display(description="потрачено, ₽", ordering="total")
    def total_display(self, trip):
        return trip.total

    @admin.display(description="участников", ordering="participants_count")
    def participants_count(self, trip):
        return trip.participants_count

    @admin.display(description="на сайте")
    def site_link(self, trip):
        return format_html(
            '<a href="{}" target="_blank">открыть</a>',
            trip.get_absolute_url(),
        )


class PaidExpenseInline(admin.TabularInline):
    """Расходы, которые оплатил участник."""

    model = Expense
    fk_name = "payer"
    extra = 0
    fields = ["title", "amount", "expense_date", "status"]
    readonly_fields = fields
    show_change_link = True
    can_delete = False
    verbose_name_plural = "оплаченные расходы"

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Participant)
class ParticipantAdmin(admin.ModelAdmin):
    list_display = ["name", "trip_link", "paid_count"]
    search_fields = ["name", "trip__name"]
    list_filter = ["trip"]
    # Поездка нужна для каждой строки: берем ее тем же запросом.
    list_select_related = ["trip"]
    ordering = ["trip__start_date", "name"]
    list_per_page = 20
    inlines = [PaidExpenseInline]

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            paid_count=Count("paid_expenses")
        )

    @admin.display(description="поездка", ordering="trip__name")
    def trip_link(self, participant):
        url = reverse("admin:trips_trip_change", args=[participant.trip_id])
        return format_html('<a href="{}">{}</a>', url, participant.trip.name)

    @admin.display(description="оплатил расходов", ordering="paid_count")
    def paid_count(self, participant):
        return participant.paid_count
