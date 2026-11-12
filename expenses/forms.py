"""Формы приложения расходов.

ExpenseFilterForm — обычная форма (forms.Form): она только проверяет
параметры поиска из адреса и ничего не сохраняет.
ExpenseForm — форма на основе модели (forms.ModelForm): по ней
создают и редактируют расходы на сайте.
"""

from decimal import Decimal

from django import forms
from django.utils import timezone

from trips.models import Participant, Trip

from .models import Category, Expense, Status
from .validators import validate_title_has_letters

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

    def full_clean(self):
        super().full_clean()
        # Поля с ошибками Bootstrap подсвечивает красным.
        for name in self.errors:
            if name in self.fields:
                widget = self.fields[name].widget
                widget.attrs["class"] += " is-invalid"


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


class ExpenseForm(BootstrapFormMixin, forms.ModelForm):
    """Создание и редактирование расхода.

    Если поездка известна заранее (расход добавляют со страницы поездки
    или редактируют), поле поездки отключено, а плательщика и участников
    можно выбрать только из этой поездки.
    """

    class Meta:
        model = Expense
        # Статус в форму не входит: расход отменяют отдельной кнопкой.
        # Признак is_large считает база.
        fields = [
            "trip",
            "title",
            "amount",
            "category",
            "expense_date",
            "payer",
            "split_between",
        ]
        labels = {
            "trip": "Поездка",
            "title": "Название",
            "amount": "Сумма, ₽",
            "category": "Категория",
            "expense_date": "Дата",
            "payer": "Кто оплатил",
            "split_between": "На кого делится",
        }
        help_texts = {
            "expense_date": "Дата должна попадать в даты поездки.",
            "split_between": "Отметьте хотя бы одного участника.",
        }
        widgets = {
            # format нужен, чтобы браузер понял текущее значение
            # при редактировании: поле type="date" ждет ГГГГ-ММ-ДД.
            "expense_date": forms.DateInput(
                attrs={"type": "date"}, format="%Y-%m-%d"
            ),
            "amount": forms.NumberInput(attrs={"min": "0.01", "step": "0.01"}),
            "split_between": forms.CheckboxSelectMultiple,
        }

    def __init__(self, *args, trip=None, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            # Поездку уже сохраненного расхода не меняют: вместе с ней
            # пришлось бы менять и всех участников.
            trip = self.instance.trip
        self.fields["title"].validators.append(validate_title_has_letters)
        # В выпадающем списке у участника пишется и поездка,
        # поэтому берем ее тем же запросом.
        people = Participant.objects.select_related("trip")
        if trip is not None:
            self.fields["trip"].initial = trip
            self.fields["trip"].disabled = True
            people = people.filter(trip=trip)
            # Все участники из одной поездки: достаточно имени.
            for name in ("payer", "split_between"):
                self.fields[name].label_from_instance = (
                    lambda person: person.name
                )
        self.fields["payer"].queryset = people
        self.fields["split_between"].queryset = people
        if not self.instance.pk:
            # Пустая форма: дата по умолчанию — сегодня.
            self.fields["expense_date"].initial = timezone.localdate()

    def clean(self):
        """Проверки, которым нужны сразу несколько полей."""
        data = super().clean()
        trip = data.get("trip")
        if trip is None:
            return data
        self.check_date(trip, data.get("expense_date"))
        self.check_people(trip, data.get("split_between"))
        self.check_duplicate(trip, data)
        return data

    def check_date(self, trip, expense_date):
        """Расход сделан в дни поездки."""
        if expense_date is None:
            return
        if not trip.start_date <= expense_date <= trip.end_date:
            self.add_error(
                "expense_date",
                f"Поездка «{trip.name}» идет с "
                f"{trip.start_date:%d.%m.%Y} по {trip.end_date:%d.%m.%Y}, "
                "дата расхода должна попадать в эти дни.",
            )

    def check_people(self, trip, people):
        """Расход делится только между участниками этой поездки."""
        if people is None:
            return
        strangers = [person for person in people if person.trip_id != trip.pk]
        if strangers:
            names = ", ".join(person.name for person in strangers)
            self.add_error(
                "split_between",
                f"Эти участники не из поездки «{trip.name}»: {names}.",
            )

    def check_duplicate(self, trip, data):
        """Один и тот же расход нельзя внести в расчет дважды.

        Дубликатом считается действующий расход той же поездки с тем же
        названием, датой и суммой. Отмененные расходы не мешают: они
        не входят в расчет. Редактируемый расход сам себе не дубликат.
        """
        title = data.get("title")
        if not (title and data.get("amount") and data.get("expense_date")):
            return
        if self.instance.pk and self.instance.is_cancelled:
            return
        # Отбор делает база, а названия сравниваем в Python: SQLite
        # не умеет сравнивать кириллицу без учета регистра.
        same_titles = (
            Expense.objects.active()
            .for_trip(trip.pk)
            .filter(amount=data["amount"], expense_date=data["expense_date"])
            .exclude(pk=self.instance.pk)
            .values_list("title", flat=True)
        )
        wanted = title.strip().casefold()
        if any(other.strip().casefold() == wanted for other in same_titles):
            # Ошибка не одного поля, а всей формы.
            self.add_error(
                None,
                "Такой расход уже учтен в поездке: то же название, "
                "дата и сумма. Если это другой расход, уточните название.",
            )
