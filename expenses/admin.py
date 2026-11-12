"""Админка расходов."""

from django import forms
from django.contrib import admin, messages
from django.urls import reverse
from django.utils.html import format_html

from trips.models import Participant

from .models import Expense, Status


class ExpenseAdminForm(forms.ModelForm):
    """Проверяет, что плательщик и участники из той же поездки."""

    class Meta:
        model = Expense
        fields = "__all__"

    def clean(self):
        data = super().clean()
        trip = data.get("trip")
        people = data.get("split_between")
        if trip is None or people is None:
            return data
        strangers = [person for person in people if person.trip_id != trip.pk]
        if strangers:
            names = ", ".join(person.name for person in strangers)
            self.add_error(
                "split_between",
                f"Эти участники не из поездки «{trip.name}»: {names}.",
            )
        return data


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    form = ExpenseAdminForm
    list_display = [
        "title",
        "trip_link",
        "payer_name",
        "category",
        "amount",
        "expense_date",
        "large",
        "status",
    ]
    list_display_links = ["title"]
    # Статус можно менять прямо в списке.
    list_editable = ["status"]
    list_filter = [
        "status",
        "category",
        ("is_large", admin.BooleanFieldListFilter),
        "trip",
    ]
    search_fields = ["title", "payer__name", "trip__name"]
    date_hierarchy = "expense_date"
    ordering = ["-expense_date", "pk"]
    list_per_page = 20
    # Поездка и плательщик для каждой строки — тем же запросом.
    list_select_related = ["trip", "payer"]
    filter_horizontal = ["split_between"]
    readonly_fields = ["large"]
    fieldsets = [
        (None, {"fields": ["trip", "title", "amount", "category"]}),
        ("Кто платил и на кого делится", {
            "fields": ["expense_date", "payer", "split_between"],
        }),
        ("Статус и чек", {"fields": ["status", "large", "receipt"]}),
    ]
    actions = ["cancel_expenses", "restore_expenses"]

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        # В выпадающем списке у участника пишется и поездка,
        # поэтому берем ее тем же запросом.
        if db_field.name == "payer":
            kwargs["queryset"] = Participant.objects.select_related("trip")
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == "split_between":
            kwargs["queryset"] = Participant.objects.select_related("trip")
        return super().formfield_for_manytomany(db_field, request, **kwargs)

    @admin.display(description="поездка", ordering="trip__name")
    def trip_link(self, expense):
        url = reverse("admin:trips_trip_change", args=[expense.trip_id])
        return format_html('<a href="{}">{}</a>', url, expense.trip.name)

    @admin.display(description="оплатил", ordering="payer__name")
    def payer_name(self, expense):
        return expense.payer.name

    # Галочка вместо слов True/False.
    @admin.display(description="крупный", boolean=True, ordering="is_large")
    def large(self, expense):
        return expense.is_large

    @admin.action(description="Отменить выбранные расходы")
    def cancel_expenses(self, request, queryset):
        count = queryset.active().update(status=Status.CANCELLED)
        self.message_user(
            request, f"Отменено расходов: {count}.", messages.SUCCESS
        )

    @admin.action(description="Вернуть выбранные расходы в расчет")
    def restore_expenses(self, request, queryset):
        count = queryset.cancelled().update(status=Status.ACTIVE)
        self.message_user(
            request, f"Возвращено расходов: {count}.", messages.SUCCESS
        )
