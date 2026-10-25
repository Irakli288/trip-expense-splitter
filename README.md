# Сервис распределения расходов поездки

## Назначение

Приложение помогает группе людей, путешествующих вместе, учитывать общие
расходы поездки и честно делить их между участниками. Сервис считает долю
каждого, показывает, кто сколько переплатил или недоплатил, и формирует
итоговый расчет: кто, кому и сколько должен перевести. Это избавляет от
ручных подсчетов в заметках и споров после поездки.

Консольная версия приложения (ПР3) дополнена веб-интерфейсом на Django (ПР5):
поездки, расходы и итоговый расчет можно просматривать в браузере.
В ПР6 страницы переведены на шаблоны Django.

## Используемые технологии

- Python 3;
- Django 5.2 — веб-фреймворк;
- Django Template Language — шаблоны страниц;
- HTML5 — разметка веб-страниц;
- CSS3 и Bootstrap 5.3 (подключается через CDN) — оформление страниц;
- JavaScript — небольшое поведение интерфейса;
- JSON — хранение данных;
- pytest — автоматизированные тесты;
- flake8 — проверка качества кода.

## Целевая аудитория

- друзья и семьи, которые вместе отправляются в отпуск или поход;
- студенческие группы на выездных мероприятиях;
- коллеги в командировках с общими тратами;
- организаторы групповых туров, которым нужно вести общий бюджет.

## Предметная область

Совместные поездки и учет общих трат. Группа создает поездку с датами и
бюджетом, добавляет участников и по ходу поездки вносит расходы: жилье,
транспорт, еду, билеты. Каждый расход оплачивает один из участников, а
делится он между всеми или частью группы. По итогам сервис рассчитывает
балансы участников и минимальный набор переводов для взаиморасчета.

## Основные сущности

| Сущность | Класс | Назначение |
|---|---|---|
| Поездка | `Trip` | название, даты и бюджет совместной поездки |
| Участник | `Participant` | человек, который едет в поездку |
| Расход | `Expense` | трата: кто оплатил и между кем она делится |
| Расчет | `Settlement` | балансы участников и переводы «кто → кому → сколько» |

## Возможности

- создание поездок с датами и бюджетом, список поездок по дате начала;
- выбор текущей поездки;
- добавление участников (без повторов имен внутри поездки);
- добавление расхода: сумма, категория, кто оплатил, между кем делится;
- удаление расхода;
- просмотр расходов с сортировкой по сумме, отбором по категории и итогами по категориям;
- контроль бюджета поездки (предупреждение при 80% и при превышении);
- расчет баланса каждого участника и списка переводов «кто → кому → сколько»;
- сохранение всех данных в JSON-файлах и загрузка при запуске;
- обработка некорректного ввода и ошибок файлов без аварийного завершения.

## Веб-интерфейс (ПР5–ПР6)

Django добавлен к существующему проекту: `manage.py` лежит в корне
репозитория рядом с `main.py`, а код ПР3 (пакет `models`, `storage.py`,
JSON-файлы, тесты, консольное меню) сохранен и продолжает работать.
Данные пока хранятся в JSON: Django ORM, Django-модели и база данных
не используются, формы еще не реализованы. Страницы строятся по объектам
`Trip`, `Participant`, `Expense` и `Settlement`, которые `storage.py`
загружает из JSON.

В ПР6 веб-интерфейс переведен на шаблоны Django (Django Template Language).
View-функции больше не собирают HTML-строки: они загружают данные,
готовят словарь контекста и вызывают `render()`, а HTML формирует шаблон.
Функция `page()` из ПР5 удалена.

```
Было (ПР5):  view → content = f"""HTML""" → page() → HttpResponse
Стало (ПР6): view → context → render() → шаблон страницы → base.html
```

### Django-проект и приложения

- `splitter/` — пакет конфигурации Django-проекта: `settings.py`
  (приложения в `INSTALLED_APPS`, каталог шаблонов проекта в
  `TEMPLATES["DIRS"]`, `LANGUAGE_CODE = "ru-RU"`,
  `TIME_ZONE = "Europe/Moscow"`), корневой `urls.py`, `asgi.py`, `wsgi.py`;
- `homepage` — главная страница и статические файлы сайта;
- `trips` — поездки: список, страница поездки с участниками и расходами,
  расчет «кто кому должен»;
- `expenses` — расходы: список всех расходов и страница расхода.

Для участников отдельное приложение не создается: участник всегда
принадлежит поездке, поэтому участники показываются на странице поездки.
Расчет (`Settlement`) тоже строится по поездке и находится в приложении
`trips`.

### Страницы и URL

| URL | Имя маршрута | View-функция | Шаблон |
|---|---|---|---|
| `/` | `homepage:index` | `homepage.views.index` | `homepage/index.html` |
| `/trips/` | `trips:list` | `trips.views.trips` | `trips/trip_list.html` |
| `/trips/<int:trip_id>/` | `trips:detail` | `trips.views.trip_detail` | `trips/trip_detail.html` |
| `/trips/<int:trip_id>/settlement/` | `trips:settlement` | `trips.views.trip_settlement` | `trips/trip_settlement.html` |
| `/expenses/` | `expenses:list` | `expenses.views.expenses` | `expenses/expense_list.html` |
| `/expenses/<int:expense_id>/` | `expenses:detail` | `expenses.views.expense_detail` | `expenses/expense_detail.html` |

Маршрутизация двухуровневая: корневой `splitter/urls.py` подключает
`homepage.urls`, `trips.urls` и `expenses.urls` через `include()`.
В `urls.py` каждого приложения задано пространство имен `app_name`
(`homepage`, `trips`, `expenses`) и имена маршрутов, поэтому ссылки
в шаблонах строятся тегом `{% url %}`, а не записываются адресами:

```
{% url 'trips:list' %}
{% url 'trips:detail' trip.id %}
{% url 'trips:settlement' trip.id %}
{% url 'expenses:detail' expense.id %}
```

Если поездка или расход с указанным номером не найдены, view-функция
передает в шаблон `None` и вызывает `render(..., status=404)`: шаблон
через `{% if %}` / `{% else %}` выводит сообщение «Поездка не найдена»
или «Расход не найден», а ответ имеет код 404. Для адресов без маршрута
Django использует шаблон `templates/404.html` (виден при `DEBUG = False`).

### Шаблоны

```
templates/                          # шаблоны уровня проекта
├── base.html                       # общий каркас всех страниц
├── 404.html                        # страница «404 – страница не найдена»
└── includes/
    └── navigation.html             # навигационная панель
homepage/templates/homepage/
└── index.html
trips/templates/trips/
├── trip_list.html
├── trip_detail.html
├── trip_settlement.html
└── includes/
    ├── trip_card.html              # карточка одной поездки
    └── budget_badge.html           # отметка «потрачено из бюджета»
expenses/templates/expenses/
├── expense_list.html
├── expense_detail.html
└── includes/
    └── category_badge.html         # отметка категории расхода
```

**Базовый шаблон и наследование.** `templates/base.html` содержит
`<!DOCTYPE html>`, кодировку, `viewport`, подключение Bootstrap и
собственного CSS, навигацию, основной контейнер, подвал и подключение
JavaScript. Дочерние шаблоны начинаются с `{% extends "base.html" %}`
и переопределяют блоки `{% block title %}` (заголовок вкладки) и
`{% block content %}` (содержимое страницы).

**Включаемые шаблоны.** Повторяющиеся фрагменты подключаются через
`{% include %}`:

- `includes/navigation.html` — навигация, подключается в `base.html`;
  активный раздел подсвечивается по `request.resolver_match.app_name`;
- `trips/includes/trip_card.html` — карточка поездки в списке поездок,
  подключается с параметрами:
  `{% include "trips/includes/trip_card.html" with trip=row.trip total=row.total budget_level=row.budget_level %}`;
- `trips/includes/budget_badge.html` — цветная отметка бюджета
  (в списке поездок и на странице поездки);
- `expenses/includes/category_badge.html` — категория расхода
  (в списке расходов, на странице расхода и в таблице расходов поездки).

**Контекст.** View-функции передают данные словарем контекста, например
в `trips.views.trips`:

```python
context = {
    "trip_rows": trip_rows,   # [{"trip": Trip, "total": ..., "budget_level": ...}]
}
return render(request, "trips/trip_list.html", context)
```

В шаблоне к атрибутам объектов обращаются через точку:
`{{ trip.name }}`, `{{ expense.payer.name }}`, `{{ expense.trip.name }}`.

**Циклы и условия.** Списки выводятся циклом `{% for %}`, пустая
коллекция обрабатывается веткой `{% empty %}` («Поездок пока нет»,
«Участников нет», «Расходы не найдены.», «Переводы не нужны»). Переводы
расчета перебираются с распаковкой кортежа:
`{% for debtor, creditor, amount in transfers %}`. Условия `{% if %}`
выбирают цвет отметки бюджета по `budget_level`, цвет баланса участника
(`row.balance > 0`, `< 0`, `= 0`) и ветку «объект не найден».

Уровень расходования бюджета вычисляет метод `Trip.budget_level(total)`
(добавлен в ПР6): `none`, `ok`, `warning` (80% и больше) или `over`.
Логика остается в классе предметной области, а шаблон только выбирает
по уровню CSS-класс.

### Фильтры шаблонов

Фильтры применяются для представления данных и не содержат бизнес-логику:

| Фильтр | Где | Что делает |
|---|---|---|
| `length` | `{{ trip_rows\|length }}`, `{{ participants\|length }}`, `{{ expenses\|length }}` | количество поездок, участников, расходов |
| `default` | `{{ trip.name\|default:"Без названия" }}` | значение, если название пустое |
| `date` | `{{ trip.start_date\|date:"d.m.Y" }}` | дата в формате 03.11.2026 |
| `floatformat` | `{{ expense.amount\|floatformat:"2g" }} ₽` | сумма с двумя знаками и разделением разрядов: 25 500,00 ₽ |
| `capfirst` | `{{ expense.category\|capfirst }}` | категория с заглавной буквы |

### Статические файлы

Собственные статические файлы лежат в приложении `homepage`:

```
homepage/static/homepage/
├── css/style.css      # собственные стили: карточки поездок, отметки, подвал
├── js/main.js         # выводит текущий год в подвале
└── img/logo.png       # логотип сервиса: чемодан и монета
```

`base.html` и `navigation.html` начинаются с `{% load static %}` и
подключают файлы тегом `{% static %}`:

```
{% static 'homepage/css/style.css' %}
{% static 'homepage/img/logo.png' %}
{% static 'homepage/js/main.js' %}
```

Bootstrap 5.3 подключается через CDN и отвечает за базовую верстку;
собственный CSS оформляет классы проекта `.trip-card`, `.budget-badge`,
`.balance-badge`, `.category-badge`, `.splitter-logo`, `.site-footer`.
Найти файл можно командой `python manage.py findstatic homepage/img/logo.png`.

### View-функции

View-функции не дублируют логику ПР3, а вызывают ее:

- `storage.load_all()` загружает поездки, участников и расходы со связями;
- `find_trip_by_id()` и `find_expense_by_id()` находят объект по номеру
  из URL;
- `sort_trips()`, `sort_expenses()`, `get_trip_participants()`,
  `iter_trip_expenses()`, `get_total()`, `Trip.check_budget()`,
  `Trip.budget_level()` дают данные страниц поездок и расходов;
- `Settlement.get_balances()`, `get_transfers()` и
  `get_settlement_status()` формируют страницу расчета.

Отложены до появления форм и POST-запросов: создание поездки, добавление
участника, добавление и удаление расхода, отбор расходов по категории.
Эти операции по-прежнему доступны в консольной версии.

## Объектная модель (ПР3)

Классы находятся в пакете `models` и импортируются из него:
`from models import Trip, Participant, Expense, Settlement`.

### Trip — поездка

Атрибуты: `id`, `name`, `start_date` и `end_date` (объекты `date`), `budget`.

Методы:

- `duration` — длительность поездки в днях (свойство, `@property`);
- `check_budget(total_amount)` — сравнение суммы расходов с бюджетом;
- `budget_level(total_amount)` — уровень расходования бюджета для
  отметки в веб-интерфейсе (ПР6);
- `validate_dates(start_date, end_date)` — проверка дат (`@staticmethod`),
  конструктор не создает поездку, которая заканчивается раньше начала;
- `__str__()` — «Поездка в Казань: 03.11.2026 – 06.11.2026 (4 дн.), бюджет 60000.00 ₽».

### Participant — участник

Атрибуты: `id`, `name`, `trip` — ссылка на объект `Trip`.

Методы:

- `from_data(data, trip)` — создание участника из записи JSON (`@classmethod`);
- `__str__()` — «Ираклий (Поездка в Казань)».

### Expense — расход

Атрибуты: `id`, `trip` (объект `Trip`), `title`, `amount`, `category`, `date`,
`payer` (объект `Participant`), `split_between` (список объектов `Participant`).

Методы:

- `share` — доля одного участника в расходе (свойство);
- `is_shared_with(participant)` — участвует ли участник в разделе расхода;
- `validate_category(category)` — проверка категории (`@staticmethod`);
- `__str__()` — строка с суммой, категорией, плательщиком и участниками.

Конструктор проверяет сумму, категорию и непустой список участников
и при ошибке выбрасывает `ValueError`.

### Settlement — расчет

Атрибуты: `trip`, `participants`, `expenses`.

Методы:

- `get_balances()` — баланс каждого участника `{Participant: сумма}`;
- `get_transfers()` — переводы `(должник, получатель, сумма)`;
- `__str__()` — статусы участников и список переводов для вывода в меню.

### Взаимодействие объектов

```
Expense ──trip──────────→ Trip
   ├──payer─────────────→ Participant ──trip──→ Trip
   └──split_between─────→ [Participant, ...]

Settlement ──→ Trip, [Participant, ...], [Expense, ...]
```

Расход хранит ссылки на объекты, поэтому данные связанных объектов доступны
напрямую: `expense.payer.name`, `expense.trip.budget`. `Settlement` получает
участников и расходы поездки и считает, кто кому должен.

В программе используются коллекции объектов: `list[Trip]`,
`list[Participant]`, `list[Expense]`. Функции модулей пакета `models`
(поиск, отбор, сортировка, добавление, вывод) работают с этими коллекциями,
а операции над одним объектом выполняются его методами.

### Что стало с функциями ПР2

| Функция ПР2 | В ПР3 |
|---|---|
| `get_trip_duration()` | свойство `Trip.duration` |
| `check_budget()` | метод `Trip.check_budget()` |
| `add_trip()`, `add_participant()`, `add_expense()` | создают объект класса, добавляют его в коллекцию и возвращают |
| `get_trip()`, `find_trips()`, `sort_trips()` | работают со списком объектов `Trip` |
| `get_trip_participants()` | отбирает объекты `Participant` по ссылке на поездку |
| `get_names()` | больше не нужна: имя берется из `participant.name` |
| `delete_expense()`, `iter_trip_expenses()`, `filter_by_category()`, `sort_expenses()`, `get_total()`, `get_totals_by_category()` | работают с объектами `Expense` |
| `calculate_balances()` | метод `Settlement.get_balances()` |
| `make_transfers()` | функция, вызывается из `Settlement.get_transfers()` |
| `calculate_share()`, `calculate_balance()`, `get_settlement_status()` | остались функциями (ПР1) |
| `show_trips()`, `show_participants()`, `show_expenses()` | перенесены из `main.py` в модули `models` |
| `show_settlement()` | заменена выводом `print(Settlement(...))` |
| `load_*()` / `save_*()` | остались в `storage.py`, создают объекты и превращают их обратно в записи |
| `input_*()`, `parse_*()`, `format_money()` | остались вспомогательными функциями `utils.py` |

## Структура проекта

```
trip-expense-splitter/
├── README.md
├── requirements.txt
├── pytest.ini              # настройки pytest
├── .flake8                 # настройки flake8
├── manage.py               # управление Django-проектом
├── main.py                 # консольная версия: точка запуска и меню
├── storage.py              # JSON ↔ объекты
├── utils.py                # разбор сумм и дат, безопасный ввод
├── splitter/               # конфигурация Django-проекта
│   ├── settings.py         # TEMPLATES["DIRS"] = [BASE_DIR / "templates"]
│   ├── urls.py             # корневые маршруты
│   ├── asgi.py
│   └── wsgi.py
├── templates/              # шаблоны уровня проекта
│   ├── base.html
│   ├── 404.html
│   └── includes/
│       └── navigation.html
├── homepage/               # Django-приложение: главная и статика
│   ├── static/homepage/
│   │   ├── css/style.css
│   │   ├── js/main.js
│   │   └── img/logo.png
│   ├── templates/homepage/
│   │   └── index.html
│   ├── urls.py
│   ├── views.py
│   └── tests.py
├── trips/                  # Django-приложение: поездки и расчет
│   ├── templates/trips/
│   │   ├── trip_list.html
│   │   ├── trip_detail.html
│   │   ├── trip_settlement.html
│   │   └── includes/
│   │       ├── trip_card.html
│   │       └── budget_badge.html
│   ├── urls.py
│   ├── views.py
│   └── tests.py
├── expenses/               # Django-приложение: расходы
│   ├── templates/expenses/
│   │   ├── expense_list.html
│   │   ├── expense_detail.html
│   │   └── includes/
│   │       └── category_badge.html
│   ├── urls.py
│   ├── views.py
│   └── tests.py
├── models/                 # классы предметной области (ПР3)
│   ├── __init__.py         # импорт классов из пакета
│   ├── trips.py            # Trip и функции работы с поездками
│   ├── participants.py     # Participant и функции работы с участниками
│   ├── expenses.py         # Expense и функции работы с расходами
│   └── settlement.py       # Settlement, балансы и переводы
├── data/
│   ├── trips.json
│   ├── participants.json
│   └── expenses.json
└── tests/
    ├── conftest.py         # общие объекты для тестов
    ├── test_trips.py
    ├── test_participants.py
    ├── test_expenses.py
    ├── test_settlement.py
    └── test_storage.py
```

## Формат данных

Данные хранятся в каталоге `data/` в виде списков записей. Формат файлов
не изменился по сравнению с ПР2. При загрузке `storage.py` превращает записи
в объекты и восстанавливает связи: по `trip_id` находит объект `Trip`,
по `payer_id` и `split_between` — объекты `Participant`. При сохранении
объекты снова превращаются в записи, а ссылки — в номера. Запись, которая
ссылается на несуществующую поездку или участника, пропускается
с предупреждением.

`trips.json`:

```json
[
    {"id": 1, "name": "Поездка в Казань", "start_date": "2026-11-03",
     "end_date": "2026-11-06", "budget": 60000.0}
]
```

`participants.json`:

```json
[
    {"id": 1, "trip_id": 1, "name": "Ираклий"}
]
```

`expenses.json` (`split_between` — номера участников, между которыми делится расход):

```json
[
    {"id": 1, "trip_id": 1, "title": "Аренда квартиры", "amount": 25500.0,
     "category": "жилье", "date": "2026-11-03", "payer_id": 1,
     "split_between": [1, 2, 3]}
]
```

Категории расходов: жилье, транспорт, еда, развлечения, прочее.

## История

- **ПР1** — начальный сценарий: один расход делится между тремя участниками.
- **ПР2** — консольное приложение с несколькими поездками, участниками и
  расходами, модули, обработка исключений, хранение данных в JSON, тесты.
  Функции ПР1 сохранены и используются в новых модулях.
- **ПР3** — объектная модель: классы `Trip`, `Participant`, `Expense`,
  `Settlement`, коллекции объектов вместо словарей, загрузка JSON в объекты,
  тесты адаптированы к классам.
- **ПР5** — Django-проект `splitter` и приложения `homepage`, `trips`,
  `expenses`: маршрутизация URL, view-функции, страницы на HTML и
  Bootstrap с данными объектов ПР3, собственная страница 404.
- **ПР6** — шаблоны Django: базовый шаблон `base.html` и наследование,
  блоки, включаемые шаблоны, передача данных через контекст, циклы и
  условия, именованные URL с пространствами имен, фильтры, собственные
  CSS, JavaScript и логотип; функция `page()` удалена.

## Требования

- Python 3.10+;
- Django 5.2;
- pytest;
- flake8.

Установка зависимостей:

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Запуск программы

Веб-версия (Django):

```bash
python manage.py migrate      # служебные таблицы Django, один раз
python manage.py check
python manage.py runserver
```

После запуска открыть в браузере http://127.0.0.1:8000/.

Консольная версия (сохранена):

```bash
python main.py
```

Пример расчета для поездки в Казань (пункт 10 меню выводит объект `Settlement`):

```
Выберите действие: 10
Ираклий: ему должны вернуть 9500.00 ₽
Анна: ему должны вернуть 3500.00 ₽
Максим: должен перевести 13000.00 ₽

Переводы:
  Максим → Ираклий: 9500.00 ₽
  Максим → Анна: 3500.00 ₽
```

## Запуск тестов

```bash
pytest -v                  # тесты предметной области (ПР1–ПР3)
python manage.py test      # тесты веб-страниц (ПР5–ПР6)
```

Тесты проверяют создание объектов и значения атрибутов, методы и `__str__`
классов, поиск, отбор и сортировку коллекций, связь расхода с поездкой
и участниками, расчет балансов и переводов, сохранение объектов в JSON
и восстановление связей при загрузке. Тесты Django-приложений проверяют,
что каждая страница открывается нужным шаблоном, показывает данные из JSON,
подключает статические файлы, что имена маршрутов дают правильные адреса
и что для несуществующих номеров и адресов возвращается 404.

## Проверка качества кода

```bash
flake8 . --extend-exclude=venv
```

## План развития

На следующих этапах планируется:

- перенос `Trip`, `Participant` и `Expense` в Django ORM и подключение базы
  данных вместо JSON-файлов;
- формы Django для создания поездок, участников и расходов;
- реализация пользователей, регистрации и разграничения доступа к поездкам;
- разработка REST API;
- контейнеризация приложения в Docker;
- настройка CI/CD и автоматических тестов.
