"""Формы приложения расходов.

ExpenseFilterForm — обычная форма (forms.Form): она только проверяет
параметры поиска из адреса и ничего не сохраняет.
"""

from decimal import Decimal

from django import forms

from trips.models import Trip

from .models import Category, Status

# Какие сортировки можно выбрать в списке расходов. В order_by()
# попадают только поля из этого словаря, а не то, что пришло в адресе.
SORT_OPTIONS = {
    "date": ("Сначала ранние", ["expense_date", "pk"]),
    "-date": ("Сначала поздние", ["-expense_date", "-pk"]),
    "amount": ("Сначала дешевые", ["amount", "pk"]),
    "-amount": ("Сначала дорогие", ["-amount", "pk"]),
    "title": ("По названию", ["title", "pk"]),
    "trip": ("По поездке", ["trip__name", "expense_date", "pk"]),
}
DEFAULT_SORT = "date"


class BootstrapFormMixin:
    """Добавляет полям формы классы Bootstrap.

    Так шаблону не нужно знать, какой виджет у какого поля:
    у списков класс form-select, у галочек form-check-input,
    у остальных полей form-control.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            widget = field.widget
            if isinstance(widget, forms.CheckboxSelectMultiple):
                css_class = "form-check-input"
            elif isinstance(widget, forms.Select):
                css_class = "form-select"
            else:
                css_class = "form-control"
            widget.attrs["class"] = css_class


class ExpenseFilterForm(BootstrapFormMixin, forms.Form):
    """Поиск, отбор и сортировка в списке расходов (GET-параметры)."""

    # Имена полей совпадают с прежними параметрами адреса (ПР9),
    # поэтому старые ссылки вида ?trip=1&sort=-amount продолжают работать.
    q = forms.CharField(
        required=False,
        max_length=100,
        label="Поиск",
        widget=forms.TextInput(attrs={
            "type": "search",
            "placeholder": "Название расхода, плательщик или поездка",
        }),
    )
    trip = forms.ModelChoiceField(
        queryset=Trip.objects.only("name").order_by("start_date", "pk"),
        required=False,
        label="Поездка",
        empty_label="Все поездки",
    )
    category = forms.ChoiceField(
        choices=[("", "Все категории")] + Category.choices,
        required=False,
        label="Категория",
    )
    status = forms.ChoiceField(
        choices=[("", "Все")] + Status.choices,
        required=False,
        label="Статус",
    )
    min_amount = forms.DecimalField(
        required=False,
        min_value=Decimal("0"),
        max_digits=12,
        decimal_places=2,
        label="Сумма от, ₽",
        widget=forms.NumberInput(attrs={"min": 0, "step": "0.01"}),
    )
    sort = forms.ChoiceField(
        choices=[(key, label) for key, (label, _) in SORT_OPTIONS.items()],
        required=False,
        label="Сортировка",
    )

    def clean_q(self):
        # Пробелы по краям не участвуют в поиске.
        return self.cleaned_data["q"].strip()

    def clean_sort(self):
        # Пустая сортировка — сортировка по умолчанию.
        return self.cleaned_data["sort"] or DEFAULT_SORT
