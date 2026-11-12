# Сервис распределения расходов поездки

## Назначение

Приложение помогает группе людей, путешествующих вместе, учитывать общие
расходы поездки и честно делить их между участниками. Сервис считает долю
каждого, показывает, кто сколько переплатил или недоплатил, и формирует
итоговый расчет: кто, кому и сколько должен перевести. Это избавляет от
ручных подсчетов в заметках и споров после поездки.

Консольная версия приложения (ПР3) дополнена веб-интерфейсом на Django (ПР5):
поездки, расходы и итоговый расчет можно просматривать в браузере.
В ПР6 страницы переведены на шаблоны Django. В ПР7 данные перенесены
из JSON в базу SQLite: страницы сайта получали их SQL-запросами.
В ПР9 данные описаны моделями Django, а страницы получают их через
Django ORM.

## Используемые технологии

- Python 3;
- Django 5.2 — веб-фреймворк, формы Django (ПР11);
- Django Template Language — шаблоны страниц;
- HTML5 — разметка веб-страниц;
- CSS3 и Bootstrap 5.3 (подключается через CDN) — оформление страниц;
- JavaScript — небольшое поведение интерфейса;
- SQLite — база данных;
- Pillow — проверка и хранение загруженных изображений (ПР11);
- Django ORM — модели, миграции и запросы к базе (ПР9);
- модуль `sqlite3` и SQL — исходная база ПР7 и перенос данных из нее;
- JSON — исходные данные и хранение консольной версии;
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
- перенос данных из JSON в базу SQLite (ПР7), а из нее в базу Django (ПР9);
- поиск поездок по названию;
- поиск расходов по названию, плательщику и поездке, отбор по поездке,
  категории и минимальной сумме, сортировка и постраничный вывод (ПР9);
- статистика: итоги по категориям, кто сколько оплатил, крупные категории,
  поездки с почти исчерпанным бюджетом;
- добавление, редактирование и отмена расхода на сайте через формы Django
  с проверкой данных и фото чека (ПР11);
- обработка некорректного ввода и ошибок файлов без аварийного завершения.

## Веб-интерфейс (ПР5–ПР6)

Django добавлен к существующему проекту: `manage.py` лежит в корне
репозитория рядом с `main.py`, а код ПР3 (пакет `models`, `storage.py`,
JSON-файлы, тесты, консольное меню) сохранен и продолжает работать.
До ПР7 страницы строились по объектам `Trip`, `Participant`, `Expense`
и `Settlement`, которые `storage.py` загружал из JSON. В ПР7 страницы
получали данные SQL-запросами из базы SQLite, с ПР9 — через модели
Django и ORM (раздел «Модели Django и ORM (ПР9)»). С ПР11 расходы
добавляют, редактируют и отменяют на сайте через формы Django
(раздел «Формы Django (ПР11)»).

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
| `/trips/<slug:slug>/` | `trips:detail` | `trips.views.trip_detail` | `trips/trip_detail.html` |
| `/trips/<slug:slug>/settlement/` | `trips:settlement` | `trips.views.trip_settlement` | `trips/trip_settlement.html` |
| `/trips/<int:trip_id>/` | `trips:by_id` | `trips.views.trip_by_id` | перенаправление на `/trips/<slug>/` |
| `/expenses/` | `expenses:list` | `expenses.views.expenses` | `expenses/expense_list.html` |
| `/expenses/statistics/` | `expenses:statistics` | `expenses.views.statistics` | `expenses/statistics.html` |
| `/expenses/<int:expense_id>/` | `expenses:detail` | `expenses.views.expense_detail` | `expenses/expense_detail.html` |
| `/expenses/create/` | `expenses:create` | `expenses.views.expense_create` | `expenses/expense_form.html` |
| `/expenses/<int:expense_id>/edit/` | `expenses:update` | `expenses.views.expense_update` | `expenses/expense_form.html` |
| `/expenses/<int:expense_id>/cancel/` | `expenses:cancel` | `expenses.views.expense_cancel` (только POST) | перенаправление на страницу расхода |
| `/media/...` | — | раздача загруженных файлов при `DEBUG` | — |
| `/admin/` | `admin:index` | админка Django | шаблоны `django.contrib.admin` |

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
├── statistics.html                 # статистика расходов (ПР7)
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
  активный раздел подсвечивается по `request.resolver_match.app_name`
  (для статистики — по `request.resolver_match.view_name`);
- `trips/includes/trip_card.html` — карточка поездки в списке поездок,
  подключается в цикле `{% for trip in trips %}` и получает объект
  модели `Trip` как переменную `trip`;
- `trips/includes/budget_badge.html` — цветная отметка бюджета
  (в списке поездок и на странице поездки);
- `expenses/includes/category_badge.html` — категория расхода
  (в списке расходов, на странице расхода, в таблице расходов поездки);
  на странице статистики подключается с параметром:
  `{% include "expenses/includes/category_badge.html" with expense=item %}`.

**Контекст.** View-функции передают данные словарем контекста, например
в `trips.views.trips` (ПР9):

```python
trips_data = Trip.objects.with_totals()             # QuerySet объектов Trip
return render(request, "trips/trip_list.html", {"trips": trips_data})
```

В шаблоне к полям объекта и связанных объектов обращаются через точку:
`{{ trip.name }}`, `{{ trip.total }}`, `{{ expense.payer.name }}`,
`{{ expense.trip.name }}`.

**Циклы и условия.** Списки выводятся циклом `{% for %}`, пустая
коллекция обрабатывается веткой `{% empty %}` («Поездок пока нет»,
«Участников нет», «Расходы не найдены.», «Переводы не нужны»). Переводы
расчета перебираются с распаковкой кортежа:
`{% for debtor, creditor, amount in transfers %}`. Условия `{% if %}`
выбирают цвет отметки бюджета по `budget_level`, цвет баланса участника
(`row.balance > 0`, `< 0`, `= 0`) и ветку «объект не найден».

Уровень расходования бюджета — `none`, `ok`, `warning` (80% и больше)
или `over`. В ПР6 его вычислял метод `Trip.budget_level(total)`, в ПР7 —
SQL-выражение `CASE ... END AS budget_level`, с ПР9 — свойство
`budget_level` модели `Trip`; шаблон только выбирает по уровню CSS-класс.

### Фильтры шаблонов

Фильтры применяются для представления данных и не содержат бизнес-логику:

| Фильтр | Где | Что делает |
|---|---|---|
| `length` | `{{ trips\|length }}`, `{{ participants\|length }}`, `{{ expenses\|length }}` | количество поездок, участников, расходов |
| `default` | `{{ trip.name\|default:"Без названия" }}` | значение, если название пустое |
| `date` | `{{ trip.start_date\|date:"d.m.Y" }}`, `{{ expense.expense_date\|date:"d.m.Y" }}` (в ПР7 дату форматировал SQL, с ПР9 снова фильтр: поле модели — `DateField`) | дата в формате 03.11.2026 |
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

В ПР5–ПР6 view-функции вызывали `storage.load_all()` и функции ПР3
(`find_trip_by_id()`, `sort_trips()`, `iter_trip_expenses()`,
`get_total()` и др.). В ПР7 поиск, отбор, сортировка и подсчет итогов
выполняли SQL-запросы, с ПР9 — запросы Django ORM (см. раздел
«Модели Django и ORM (ПР9)»). Расчет «кто кому должен» по-прежнему
выполняет класс `Settlement`: функция `load_settlement()` строит объекты
`Trip`, `Participant` и `Expense` ПР3 из записей моделей Django и
вызывает `get_balances()` и `get_transfers()`.

С ПР11 расход на сайте можно добавить, изменить и отменить (формы
Django, POST-запросы). Создание поездки и добавление участника пока
доступны в админке и консольной версии.

## База данных SQLite (ПР7)

В ПР7 данные проекта перенесены из JSON-файлов в базу SQLite
`data/splitter.sqlite`, с которой страницы работали модулем `sqlite3`
без Django ORM. С ПР9 страницы работают с базой Django `db.sqlite3`
через ORM, а `data/splitter.sqlite` осталась исходной базой, из которой
данные переносятся в базу Django. Файлы SQL-слоя сохранены: на них
построены перенос данных и тесты `tests/test_database.py`.

```
До ПР7:    JSON → storage.py → объекты Python → Django view → шаблон
После ПР7: SQLite → SQL-запрос → sqlite3 → Django view → context → шаблон
```

JSON-файлы и консольная версия (`main.py`) сохранены: JSON остается
исходными данными, из которых заполняется база.

### Структура базы данных

**trips** — поездки:

| Поле | Тип | Ограничения | Назначение |
|---|---|---|---|
| `id` | INTEGER | PRIMARY KEY | номер поездки |
| `name` | TEXT | NOT NULL | название |
| `start_date` | TEXT | NOT NULL | дата начала, `YYYY-MM-DD` |
| `end_date` | TEXT | NOT NULL, `start_date <= end_date` | дата окончания |
| `budget` | REAL | может быть NULL | бюджет; NULL — бюджет не задан |

**participants** — участники:

| Поле | Тип | Ограничения | Назначение |
|---|---|---|---|
| `id` | INTEGER | PRIMARY KEY | номер участника |
| `trip_id` | INTEGER | NOT NULL, FOREIGN KEY → `trips.id` | поездка участника |
| `name` | TEXT | NOT NULL | имя |

**expenses** — расходы:

| Поле | Тип | Ограничения | Назначение |
|---|---|---|---|
| `id` | INTEGER | PRIMARY KEY | номер расхода |
| `trip_id` | INTEGER | NOT NULL, FOREIGN KEY → `trips.id` | поездка |
| `title` | TEXT | NOT NULL | название расхода |
| `amount` | REAL | NOT NULL, `amount > 0` | сумма |
| `category` | TEXT | NOT NULL, DEFAULT `'прочее'`, одна из 5 категорий | категория |
| `expense_date` | TEXT | NOT NULL | дата, `YYYY-MM-DD` |
| `payer_id` | INTEGER | NOT NULL, FOREIGN KEY → `participants.id` | кто оплатил |

**expense_shares** — доли расходов (между кем делится расход):

| Поле | Тип | Ограничения | Назначение |
|---|---|---|---|
| `expense_id` | INTEGER | NOT NULL, FOREIGN KEY → `expenses.id` | расход |
| `participant_id` | INTEGER | NOT NULL, FOREIGN KEY → `participants.id` | участник |

Первичный ключ `expense_shares` составной: `(expense_id, participant_id)` —
один участник входит в расход один раз. Таблица заменяет список
`split_between` из JSON и реализует связь «многие ко многим» между
расходами и участниками. Расчет (`Settlement`) в базе не хранится:
он вычисляется по расходам и долям.

```
trips 1 ──< participants
trips 1 ──< expenses >── 1 participants   (payer_id)
expenses 1 ──< expense_shares >── 1 participants
```

### Файлы слоя базы данных

| Файл | Назначение |
|---|---|
| `sql/schema.sql` | команды `CREATE TABLE IF NOT EXISTS` с ключами и ограничениями |
| `sql/queries.sql` | 17 проверенных SQL-запросов проекта с комментариями |
| `db/database.py` | `get_connection()`: подключение и `PRAGMA foreign_keys = ON`; `create_tables()` |
| `db/import_json.py` | перенос данных из JSON: `executemany()`, параметры `?`, `commit()` / `rollback()` |
| `db/testing.py` | временная база для тестов Django-страниц |
| `data/splitter.sqlite` | файл базы данных |

### Создание базы и перенос данных

```bash
python -m db.import_json
```

Скрипт создает таблицы по `sql/schema.sql` (если их еще нет), очищает их
и заново заполняет записями из `trips.json`, `participants.json` и
`expenses.json`, поэтому его можно запускать повторно. При ошибке
изменения откатываются (`rollback()`). Проверка в SQLite CLI:

```
sqlite3 data/splitter.sqlite
sqlite> .tables
expense_shares  expenses  participants  trips
sqlite> SELECT COUNT(*) FROM expenses;
6
sqlite> PRAGMA foreign_key_list(expenses);
```

Все запросы файла можно выполнить разом:
`sqlite3 -header -column data/splitter.sqlite < sql/queries.sql`.

### SQL-запросы (`sql/queries.sql`)

Колонка «Где использовался» показывает страницы ПР7. С ПР9 эти страницы
получают те же данные запросами ORM (таблица «Запросы ORM» ниже),
а файл сохранен как SQL-реализация предметной области.

| № | Запрос | Элементы SQL | Где использовался |
|---|---|---|---|
| 1 | список поездок | SELECT, ORDER BY | форма поиска `/expenses/` |
| 2 | участники поездки | WHERE `trip_id = ?` | `/trips/<id>/`, расчет |
| 3 | три самых крупных расхода | JOIN, ORDER BY, LIMIT | `/expenses/statistics/` |
| 4 | поиск расходов по поездке, категории, сумме | JOIN, WHERE с параметрами | `/expenses/` |
| 5 | количество и сумма найденных расходов | COUNT, SUM, WHERE | `/expenses/` |
| 6 | участники, которые еще ничего не оплачивали | WHERE, подзапрос NOT IN | `/trips/<id>/` |
| 7 | расходы поездки с плательщиком | JOIN, WHERE | `/trips/<id>/`, расчет |
| 8 | расход с поездкой и плательщиком | JOIN, WHERE `id = ?` | `/expenses/<id>/` |
| 9 | участники, между которыми делится расход | JOIN, WHERE | `/expenses/<id>/` |
| 10 | доли всех расходов поездки | JOIN, WHERE | расчет `/trips/<id>/settlement/` |
| 11 | сводка: поездки, участники, расходы, сумма | COUNT, SUM, MAX | главная `/` |
| 12 | поездки с числом участников, суммой и уровнем бюджета | LEFT JOIN, GROUP BY, SUM, CASE | `/trips/` |
| 13 | одна поездка с итогами и процентом бюджета | LEFT JOIN, WHERE, GROUP BY | `/trips/<id>/` |
| 14 | итоги по категориям | GROUP BY, COUNT, SUM, AVG, MAX | `/expenses/statistics/` |
| 15 | сколько оплатил каждый участник | JOIN, LEFT JOIN, GROUP BY | `/expenses/statistics/` |
| 16 | категории с суммой не меньше заданной | GROUP BY, HAVING `>= ?` | `/expenses/statistics/` |
| 17 | поездки, израсходовавшие 80% бюджета и больше | JOIN, GROUP BY, HAVING | `/expenses/statistics/` |

Пример запроса с соединением таблиц и группировкой (запрос 15):

```sql
SELECT
    participants.name AS participant_name,
    trips.name AS trip_name,
    COUNT(expenses.id) AS expenses_count,
    COALESCE(SUM(expenses.amount), 0) AS paid_total
FROM participants
JOIN trips
    ON participants.trip_id = trips.id
LEFT JOIN expenses
    ON expenses.payer_id = participants.id
GROUP BY participants.id
ORDER BY paid_total DESC, participants.name;
```

## Модели Django и ORM (ПР9)

В ПР9 доступ к данным переведен с ручных SQL-запросов на Django ORM.
Предметная область, страницы, шаблоны и адреса не изменились, поменялся
только источник данных во view-функциях.

```
ПР7: SQLite → SQL-запрос → sqlite3 → Django view → context → шаблон
ПР9: модели → запрос ORM → SQL → db.sqlite3 → объекты моделей → view → шаблон
```

### Стратегия перехода

Выбран вариант «таблицы под управлением Django и перенос данных».
Django работает с базой `db.sqlite3` (настройка `DATABASES`), таблицы в ней
создают миграции. База ПР7 `data/splitter.sqlite` не меняется и служит
источником: скрипт `db/import_sqlite_to_orm.py` читает ее и создает записи
через ORM. Подключать модели к старым таблицам через `db_table` не стали:
таблица `expense_shares` с составным ключом не похожа на таблицу
связи «многие ко многим», которую ожидает Django, а история миграций
для старых таблиц отсутствует.

### Модели

Модели лежат в `models.py` приложений: `Trip` и `Participant` — в `trips`
(участник всегда принадлежит поездке), `Expense` — в `expenses`.
Первичный ключ `id` Django добавляет сам (`BigAutoField`).

**Trip** (`trips/models.py`) — поездка:

| Поле | Тип | Назначение |
|---|---|---|
| `name` | `CharField(max_length=200)` | название |
| `start_date`, `end_date` | `DateField` | даты; ограничение `CheckConstraint`: начало не позже окончания |
| `budget` | `DecimalField(12, 2, null=True, blank=True)` | бюджет; пусто — бюджет не задан |

Методы и свойства: `duration` (дни поездки), `get_total()`,
`budget_level`, `used_percent`, `budget_diff`. Менеджер
`Trip.objects.with_totals()` добавляет к поездкам `total`,
`expenses_count` и `participants_count` одним запросом.

**Participant** (`trips/models.py`) — участник:

| Поле | Тип | Назначение |
|---|---|---|
| `trip` | `ForeignKey(Trip, on_delete=CASCADE, related_name="participants")` | поездка |
| `name` | `CharField(max_length=100)` | имя; `UniqueConstraint(trip, name)` — без повторов имен в поездке |

**Expense** (`expenses/models.py`) — расход:

| Поле | Тип | Назначение |
|---|---|---|
| `trip` | `ForeignKey(Trip, on_delete=CASCADE, related_name="expenses")` | поездка |
| `title` | `CharField(max_length=200)` | название |
| `amount` | `DecimalField(12, 2)`, `MinValueValidator(0.01)`, `CheckConstraint(amount > 0)` | сумма |
| `category` | `CharField(choices=Category.choices, default="прочее")`, `CheckConstraint` | категория из 5 значений |
| `expense_date` | `DateField` | дата |
| `payer` | `ForeignKey(Participant, on_delete=RESTRICT, related_name="paid_expenses")` | кто оплатил |
| `split_between` | `ManyToManyField(Participant, related_name="shared_expenses")` | между кем делится |

Метод `clean()` не дает выбрать плательщика из другой поездки,
`get_share()` считает долю участника функцией `calculate_share()` из ПР3.
У всех моделей заданы `__str__()`, `Meta.ordering`, `verbose_name`
и `verbose_name_plural`; у полей — русские `verbose_name`.

Связи:

```
Trip 1 ──< Participant            (participant.trip,  trip.participants)
Trip 1 ──< Expense                (expense.trip,      trip.expenses)
Participant 1 ──< Expense         (expense.payer,     participant.paid_expenses)
Expense >──< Participant          (expense.split_between, participant.shared_expenses)
```

Правила удаления: при удалении поездки удаляются ее участники и расходы
(`CASCADE`). Участника, который оплачивал расходы, отдельно удалить нельзя
(`RESTRICT`, ошибка `RestrictedError`), но вместе с поездкой он удаляется.
С `PROTECT` удалить такую поездку было бы нельзя совсем.

### Миграции

| Файл | Что создает |
|---|---|
| `trips/migrations/0001_initial.py` | таблицы `trips_trip`, `trips_participant` и их ограничения |
| `expenses/migrations/0001_initial.py` | таблицы `expenses_expense` и `expenses_expense_split_between` |

```bash
python manage.py makemigrations       # создать файлы миграций по моделям
python manage.py showmigrations       # какие миграции применены ([X])
python manage.py sqlmigrate expenses 0001   # посмотреть SQL миграции
python manage.py migrate              # применить миграции к db.sqlite3
python manage.py makemigrations --check     # модели и миграции совпадают
```

### Перенос данных из базы ПР7

```bash
python -m db.inspect_source_db        # таблицы, столбцы и число записей ПР7
python manage.py migrate
python -m db.import_sqlite_to_orm     # перенос в базу Django
```

Скрипт переносит поездки, потом участников, потом расходы и списки
участников расходов (`split_between.set()`), сохраняя номера записей,
поэтому связи не теряются. Записи создаются `update_or_create()`, так что
повторный запуск обновляет их, а не дублирует. Все выполняется в одной
транзакции `transaction.atomic()`. Даты из строк `YYYY-MM-DD`
превращаются в `date`, суммы — в `Decimal`. Результат: 2 поездки,
5 участников, 6 расходов — столько же, сколько в базе ПР7.

### Запросы ORM

| № | Запрос ORM | Приемы | Где |
|---|---|---|---|
| 1 | `Trip.objects.with_totals()` | `annotate()`, `Sum`, `Count`, `Coalesce`, подзапрос `Subquery` | `/trips/`, `/trips/<id>/` |
| 2 | `.filter(text_search(q, "name"))` | поиск по строковому полю `icontains` | `/trips/?q=` |
| 3 | `Trip.objects.with_totals().filter(pk=trip_id).first()` | один объект по номеру | `/trips/<id>/` |
| 4 | `trip.participants.all()` | обратная связь `related_name` | `/trips/<id>/`, расчет |
| 5 | `trip.expenses.select_related("payer")` | связанный объект одним запросом | `/trips/<id>/` |
| 6 | `trip.participants.filter(paid_expenses__isnull=True)` | фильтр по связанной модели | `/trips/<id>/` |
| 7 | `record.expenses.prefetch_related("split_between")` | связь «многие ко многим» без лишних запросов | `/trips/<id>/settlement/` |
| 8 | `Expense.objects.aggregate(Count, Sum, Max)`, `Trip.objects.count()` | сводные показатели | `/` |
| 9 | `.filter(trip_id=...)`, `.filter(category=...)`, `.filter(amount__gte=...)` | фильтр по одному и нескольким условиям | `/expenses/` |
| 10 | `.filter(text_search(q, "title", "payer__name", "trip__name"))` | поиск по нескольким полям, объекты `Q` через ИЛИ | `/expenses/?q=` |
| 11 | `.order_by(*SORT_OPTIONS[sort])` | сортировка по одному, нескольким полям и полю поездки `trip__name` | `/expenses/?sort=` |
| 12 | `found.aggregate(expenses_count=Count("pk"), expenses_total=Sum("amount"))` | итог найденного | `/expenses/` |
| 13 | `Paginator(found, 5).get_page(page)` | постраничный вывод | `/expenses/?page=` |
| 14 | `Trip.objects.only("name")` | сокращенный набор полей | список поездок в форме |
| 15 | `Expense.objects.select_related("trip", "payer").get(pk=...)` | `get()` и `DoesNotExist` → 404 | `/expenses/<id>/` |
| 16 | `expense.split_between.order_by("pk")` | связь «многие ко многим» | `/expenses/<id>/` |
| 17 | `Expense.objects.values("category").annotate(Count, Sum, Avg, Max)` | группировка по категории | статистика |
| 18 | `Participant.objects.select_related("trip").annotate(paid_total=Coalesce(Sum(...), 0))` | LEFT JOIN: участники без расходов тоже в списке | статистика |
| 19 | `.values("category").annotate(total=Sum("amount")).filter(total__gte=...)` | условие на сумму группы (HAVING) | статистика |
| 20 | `Trip.objects.with_totals().exclude(budget__isnull=True).filter(total__gte=F("budget") * 0.8)` | `exclude()`, выражение `F` | статистика |
| 21 | `Expense.objects.select_related("trip").order_by("-amount", "pk")[:3]` | сортировка и ограничение `LIMIT` | статистика |

Параметры из адреса проверяются: номер поездки и суммы — функцией
`parse_number()` (кривые, отрицательные, `nan` и бесконечность
заменяются значениями по умолчанию), категория — по списку
`Category.values`, сортировка — по словарю `SORT_OPTIONS` (в `order_by()`
не попадает то, что пришло в адресе), неверный номер страницы
`Paginator.get_page()` заменяет ближайшей существующей. Ссылки на страницы
строит тег `{% querystring page=... %}`, поэтому поиск, фильтры
и сортировка сохраняются при переходе между страницами.

SQLite сравнивает без учета регистра только латинские буквы, поэтому
функция `splitter/search.py: text_search()` ищет запрос как есть,
строчными буквами и с заглавной первой буквой: «казань» находит «Казань».

### Страницы

| Страница | Что показывает | Запросы ORM |
|---|---|---|
| Главная `/` | сводка: поездки, участники, расходы, сумма | 8 |
| Поездки `/trips/` | карточки поездок с итогами, поиск по названию | 1, 2 |
| Поездка `/trips/<id>/` | бюджет, участники, расходы, кто еще не платил | 3–6 |
| Расчет `/trips/<id>/settlement/` | балансы и переводы (класс `Settlement`) | 4, 7 |
| Расходы `/expenses/` | поиск, отбор, сортировка, страницы по 5 расходов, итог | 9–14 |
| Расход `/expenses/<id>/` | поездка, плательщик, участники, доля каждого | 15, 16 |
| Статистика `/expenses/statistics/` | категории, плательщики, крупные расходы и категории, бюджет | 17–21 |

Если поездки или расхода с таким номером нет, страница показывает
«Поездка не найдена» / «Расход не найден» с кодом 404. При пустой базе
страницы открываются и показывают нули и сообщения «Поездок пока нет»,
«Расходы не найдены.», «Данные отсутствуют.».

## Админка и анализ SQL-запросов (ПР10)

В ПР10 к проекту подключена административная панель Django, модели
получили адрес поездки латиницей, статус расхода и признак крупного
расхода, а число SQL-запросов страниц проверено панелью Django Debug
Toolbar и тестами.

### Административная панель

Админка открывается по адресу http://127.0.0.1:8000/admin/ после
создания администратора командой `python manage.py createsuperuser`.
Заголовок админки — «Сервис расходов поездки», разделы подписаны
по-русски («Поездки и участники», «Расходы»).

| Модель | Список | Поиск и фильтры | Страница записи |
|---|---|---|---|
| `Trip` (`trips/admin.py`) | название, даты, бюджет, потрачено, участников, ссылка на сайт | поиск по названию и адресу, фильтр и навигация по дате начала | группы полей, адрес заполняется из названия при вводе, участники и расходы поездки на той же странице |
| `Participant` | имя, поездка (ссылка), сколько расходов оплатил | поиск по имени и поездке, фильтр по поездке | оплаченные участником расходы |
| `Expense` (`expenses/admin.py`) | название, поездка, плательщик, категория, сумма, дата, крупный, статус (меняется прямо в списке) | поиск по названию, плательщику и поездке, фильтры по статусу, категории, крупности и поездке, навигация по датам | группы полей, выбор участников в два столбца, проверка, что плательщик и участники из той же поездки |

Действия над выбранными расходами: «Отменить выбранные расходы»
и «Вернуть выбранные расходы в расчет».

### Изменения моделей

| Модель | Что добавлено |
|---|---|
| `Trip` | поле `slug` (уникальное, заполняется из названия транслитерацией: «Поездка в Казань» → `poezdka-v-kazan`, при повторе — `-2`, `-3`), метод `get_absolute_url()`, проверка в `clean()`: адрес не из одних цифр |
| `Expense` | поле `status` (`Status`: «Учитывается» / «Отменен»), вычисляемое базой поле `is_large = GeneratedField(...)` (сумма от 10 000 ₽), `get_absolute_url()`, свойство `is_cancelled`, ограничение `expense_status_known` |
| `ExpenseQuerySet` | менеджер `Expense.objects` с методами `active()`, `cancelled()`, `for_trip()`, `search()`, `with_relations()`; методы доступны и через связь: `trip.expenses.active()` |
| все модели | `help_text` у полей, которые заполняют в админке |

Отмененный расход виден в списках серым с отметкой «Отменен», но не
входит в итоги поездки (`with_totals()`, `get_total()`), расчет долгов,
сводку на главной и статистику. Категории и статусы вынесены
в `expenses/choices.py`.

### Миграции ПР10

| Файл | Что делает |
|---|---|
| `trips/migrations/0002_trip_slug_and_help_texts.py` | добавляет `slug` (пока может быть пустым) и подсказки полей |
| `trips/migrations/0003_fill_trip_slugs.py` | `RunPython`: заполняет адреса у уже существующих поездок |
| `trips/migrations/0004_trip_slug_unique.py` | делает `slug` обязательным и уникальным |
| `expenses/migrations/0002_expense_status_is_large.py` | добавляет `status`, `is_large`, ограничение статуса и подсказки полей |

### Адреса поездок

Страница поездки теперь открывается по адресу `/trips/<slug>/`
(например, `/trips/poezdka-v-kazan/`), расчет — `/trips/<slug>/settlement/`.
Старый адрес `/trips/<номер>/` оставлен и постоянно (код 301)
перенаправляет на новый, поэтому сохраненные ссылки не ломаются.

### Обработчик контекста

`splitter/context_processors.py: site()` добавляет в каждый шаблон
название сайта `site_name` и число поездок `trips_count` для меню.
Число поездок передается методом `Trip.objects.count` без вызова, так
что запрос выполняется, только если шаблон его выводит.

### Django Debug Toolbar

Панель подключается в `splitter/settings.py`, только когда `DEBUG = True`
и не идут тесты (`TESTING`), и показывается для адреса `127.0.0.1`
(`INTERNAL_IPS`). На вкладке SQL видно каждый запрос страницы, его время
и план (`Expl`). Число запросов (без запросов сессии и пользователя):

| Страница | ПР9 | ПР10 | Что изменилось |
|---|---|---|---|
| `/` | 3 | 4 | +1 число поездок для меню |
| `/trips/` | 1 | 2 | +1 меню |
| `/trips/<slug>/` | 4 | 5 | +1 меню |
| `/trips/<slug>/settlement/` | 4 | 5 | +1 меню |
| `/expenses/` | 4 | 5 | +1 меню |
| `/expenses/<id>/` | 2 | 3 | +1 меню |
| `/expenses/statistics/` | 5 | 8 | +1 меню, таблица по статусам, число крупных расходов |

В админке (с запросами сессии и пользователя) без `list_select_related`
и `select_related()` каждая строка списка расходов делала еще два
запроса (поездка и плательщик), а каждый участник в выпадающем списке —
запрос своей поездки (`Participant.__str__`):

| Страница админки | без оптимизации | с оптимизацией |
|---|---|---|
| список расходов | 20 | 8 |
| расход | 17 | 7 |
| поездка (с участниками и расходами) | 18 | 10 |
| список участников | 11 | 6 |

Тесты `test_query_counts` и `test_list_queries_do_not_grow` проверяют
число запросов через `assertNumQueries`: после добавления 10 расходов
список в админке делает столько же запросов.

## Формы Django (ПР11)

В ПР11 на сайте появились формы: фильтр списка расходов, добавление,
редактирование и отмена расхода, загрузка фото чека. Формы описаны
в `expenses/forms.py`, свои валидаторы — в `expenses/validators.py`.

### Формы

| Форма | Класс | Где используется | Что делает |
|---|---|---|---|
| `ExpenseFilterForm` | `forms.Form` | `/expenses/` (GET) | проверяет параметры поиска, отбора и сортировки из адреса |
| `ExpenseForm` | `forms.ModelForm` (модель `Expense`) | `/expenses/create/`, `/expenses/<id>/edit/` (GET и POST) | создает и изменяет расход, проверяет данные, принимает фото чека |
| `BootstrapFormMixin` | примесь | обе формы | ставит полям классы Bootstrap и подсвечивает поля с ошибками (`is-invalid`) |

### Фильтр расходов (`ExpenseFilterForm`)

Поля формы называются так же, как GET-параметры из ПР9 (`q`, `trip`,
`category`, `status`, `min_amount`, `sort`), поэтому старые ссылки
работают. Номер страницы `page` в форму не входит: это не условие
отбора, а часть пагинации.

| Поле | Тип | Проверка |
|---|---|---|
| `q` | `CharField` | не длиннее 100 символов, пробелы по краям убирает `clean_q()` |
| `trip` | `ModelChoiceField` | поездка существует (в `cleaned_data` — объект `Trip`) |
| `category`, `status` | `ChoiceField` | значение из `Category` / `Status` |
| `min_amount` | `DecimalField(min_value=0)` | число не меньше 0 (`nan`, `abc`, `-5` не проходят) |
| `sort` | `ChoiceField` | одна из сортировок `SORT_OPTIONS`, пустое значение → `date` (`clean_sort()`) |

```python
form = ExpenseFilterForm(request.GET or None)
form_valid = form.is_bound and form.is_valid()
filters = form.cleaned_data if form_valid else {}
```

Без параметров форма не связана с данными (`is_bound = False`) — это
первое открытие страницы. Если параметры с ошибкой, фильтры не
применяются, над формой выводится предупреждение, а у поля — текст
ошибки. Выбранные значения остаются в полях, менеджер
`Expense.objects`, сортировка и пагинация остались прежними.

### Добавление и редактирование расхода (`ExpenseForm`)

В форму входят поля `trip`, `title`, `amount`, `category`,
`expense_date`, `payer`, `split_between`, `receipt`. Поле `status` в
форму не входит: расход отменяют отдельной кнопкой. Признак `is_large`
считает база.

- подписи и подсказки — `Meta.labels`, `Meta.help_texts`;
- виджеты — `DateInput(type="date")` для даты, `NumberInput` для суммы,
  `CheckboxSelectMultiple` для участников, `ClearableFileInput` для фото;
- начальное значение даты — сегодня (`initial`);
- адрес `/expenses/create/?trip=<номер>` (кнопка «Добавить расход» на
  странице поездки) выбирает поездку заранее: поле поездки отключено
  (`disabled`), а плательщика и участников можно выбрать только из нее;
- при редактировании поездку менять нельзя (поле отключено), иначе
  пришлось бы менять и всех участников.

Проверки:

| Правило | Где | Сообщение |
|---|---|---|
| сумма больше нуля | `MinValueValidator` модели | «Убедитесь, что это значение больше либо равно 0.01» |
| в названии есть буква | валидатор `validate_title_has_letters` | «Название должно содержать хотя бы одну букву.» |
| дата в днях поездки | `ExpenseForm.clean()` → `check_date()` | «Поездка «…» идет с … по …, дата расхода должна попадать в эти дни.» |
| плательщик из этой поездки | `Expense.clean()` (ПР9) | «Плательщик должен быть участником этой поездки.» |
| участники из этой поездки | `ExpenseForm.clean()` → `check_people()` | «Эти участники не из поездки «…»: …» |
| нет такого же действующего расхода (поездка, название без учета регистра, дата и сумма) | `ExpenseForm.clean()` → `check_duplicate()` | общая ошибка формы «Такой расход уже учтен в поездке…» |

Проверка дубликата берет только действующие расходы
(`Expense.objects.active()`), поэтому отмененный расход не мешает
внести такой же заново. При редактировании расход исключается из
проверки (`exclude(pk=self.instance.pk)`) и не конфликтует сам с собой.

Обработка в представлении (`expenses/views.py`):

```python
def expense_update(request, expense_id):
    expense = get_object_or_404(
        Expense.objects.select_related("trip"), pk=expense_id
    )
    if request.method == "POST":
        # instance: форма меняет этот расход, а не создает новый.
        form = ExpenseForm(request.POST, request.FILES, instance=expense)
        if form.is_valid():
            form.save()
            messages.success(request, "Изменения сохранены.")
            return redirect(expense)
    else:
        form = ExpenseForm(instance=expense)
    ...
```

Данные сохраняются только после `is_valid()`. При ошибках форма
показывается снова с введенными значениями, ошибками полей и общими
ошибками (`form.non_field_errors`). После сохранения пользователь
переходит на страницу расхода и видит сообщение (`django.contrib.messages`).
Нет такого расхода — `get_object_or_404()` возвращает 404.

### Отмена расхода

```python
@require_POST
def expense_cancel(request, expense_id):
    expense = get_object_or_404(Expense.objects.active(), pk=expense_id)
    expense.cancel()
    ...
```

`Expense.cancel()` меняет статус на «Отменен» и сохраняет только поле
`status`: запись остается в истории, но не входит в итоги и расчет
долгов. Кнопка «Отменить» в списке и на странице расхода — это
POST-форма с `{% csrf_token %}`. Открыть адрес отмены в браузере (GET)
нельзя — ответ 405, повторная отмена — ответ 404.

### CSRF

Все формы, которые меняют данные, отправляются методом POST
и содержат `{% csrf_token %}`. `CsrfViewMiddleware` отклоняет POST без
токена с ответом 403 (это проверяет тест `CsrfTests`). Фильтр расходов
ничего не меняет, поэтому отправляется методом GET.

### Фото чека

- модель: `Expense.receipt = ImageField(upload_to="receipts/%Y/%m/",
  blank=True)` с проверками расширения (`jpg`, `jpeg`, `png`, `webp`)
  и размера (не больше 5 МБ, `validate_receipt_size`); `ImageField`
  через Pillow проверяет, что файл действительно картинка;
- миграция `expenses/migrations/0003_expense_receipt.py`;
- настройки: `MEDIA_URL = "/media/"`, `MEDIA_ROOT = BASE_DIR / "media"`,
  в режиме `DEBUG` файлы раздает `static()` в `splitter/urls.py`;
- шаблон формы: `enctype="multipart/form-data"`, представление передает
  в форму `request.FILES`;
- страница расхода показывает фото или надпись «чек не приложен»;
- папка `media/` в `.gitignore`: загруженные файлы не попадают в Git;
- в админке поле есть в группе «Статус и чек».

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
├── db/                     # исходная база SQLite (ПР7) и перенос (ПР9)
│   ├── __init__.py
│   ├── database.py         # подключение к базе ПР7
│   ├── import_json.py      # перенос данных из JSON в базу ПР7
│   ├── inspect_source_db.py    # таблицы и записи базы ПР7
│   ├── import_sqlite_to_orm.py # перенос из базы ПР7 в базу Django
│   └── testing.py          # тестовые данные для Django-тестов
├── sql/
│   ├── schema.sql          # создание таблиц
│   └── queries.sql         # SQL-запросы проекта
├── utils.py                # разбор сумм и дат, безопасный ввод
├── splitter/               # конфигурация Django-проекта
│   ├── settings.py         # TEMPLATES["DIRS"], DATABASES → db.sqlite3
│   ├── urls.py             # корневые маршруты
│   ├── search.py           # поиск без учета регистра (кириллица)
│   ├── context_processors.py   # название сайта и число поездок (ПР10)
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
│   ├── models.py           # модели Trip и Participant (ПР9)
│   ├── slugs.py            # адрес поездки латиницей (ПР10)
│   ├── admin.py            # админка поездок и участников (ПР10)
│   ├── migrations/         # миграции (ПР9, ПР10)
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
│   ├── models.py           # модель Expense и ее менеджер (ПР9–ПР11)
│   ├── forms.py            # формы фильтра и расхода (ПР11)
│   ├── validators.py       # свои валидаторы полей (ПР11)
│   ├── choices.py          # категории и статусы расхода (ПР10)
│   ├── admin.py            # админка расходов (ПР10)
│   ├── migrations/         # миграции (ПР9–ПР11)
│   ├── templates/expenses/
│   │   ├── expense_list.html
│   │   ├── expense_detail.html
│   │   ├── expense_form.html   # добавление и редактирование (ПР11)
│   │   ├── statistics.html
│   │   └── includes/
│   │       ├── cancel_form.html    # кнопка отмены, POST (ПР11)
│   │       ├── category_badge.html
│   │       └── status_badge.html
│   ├── urls.py
│   ├── views.py
│   ├── tests.py
│   └── test_forms.py       # тесты форм (ПР11)
├── models/                 # классы предметной области (ПР3)
│   ├── __init__.py         # импорт классов из пакета
│   ├── trips.py            # Trip и функции работы с поездками
│   ├── participants.py     # Participant и функции работы с участниками
│   ├── expenses.py         # Expense и функции работы с расходами
│   └── settlement.py       # Settlement, балансы и переводы
├── data/
│   ├── trips.json
│   ├── participants.json
│   ├── expenses.json
│   └── splitter.sqlite     # исходная база SQLite (ПР7)
└── tests/
    ├── conftest.py         # общие объекты для тестов
    ├── test_trips.py
    ├── test_participants.py
    ├── test_expenses.py
    ├── test_settlement.py
    ├── test_storage.py
    └── test_database.py    # схема, перенос данных, запросы (ПР7)
```

## Формат данных JSON

Исходные данные хранятся в каталоге `data/` в виде списков записей. Формат файлов
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
- **ПР7** — база данных SQLite: таблицы `trips`, `participants`,
  `expenses`, `expense_shares` с первичными и внешними ключами
  (`sql/schema.sql`), перенос данных из JSON (`db/import_json.py`),
  17 SQL-запросов (`sql/queries.sql`), страницы сайта получают данные
  SQL-запросами через `sqlite3`, поиск расходов и страница статистики.
- **ПР9** — Django ORM: модели `Trip`, `Participant`, `Expense` со связями
  `ForeignKey` и `ManyToManyField`, миграции, перенос данных из базы ПР7
  в базу Django (`db/import_sqlite_to_orm.py`), страницы получают данные
  запросами ORM; поиск, сортировка и постраничный вывод списка расходов.
- **ПР10** — административная панель Django для поездок, участников
  и расходов (списки, поиск, фильтры, встроенные формы, действия),
  адрес поездки `slug`, статус расхода и вычисляемое поле `is_large`,
  менеджер `ExpenseQuerySet`, обработчик контекста, анализ SQL-запросов
  в Django Debug Toolbar и проверка их числа в тестах.
- **ПР11** — формы Django: фильтр расходов на `forms.Form`, добавление
  и редактирование расхода на `ModelForm` с проверками (дата в днях
  поездки, участники из поездки, нет дубликата среди действующих
  расходов), отмена расхода POST-запросом со сменой статуса, CSRF,
  загрузка и показ фото чека.

## Требования

- Python 3.10+;
- Django 5.2;
- django-debug-toolbar;
- Pillow (для фото чеков, `ImageField`);
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
python manage.py migrate              # создать таблицы в db.sqlite3
python -m db.import_sqlite_to_orm     # перенести данные из базы ПР7
python manage.py createsuperuser      # администратор для /admin/
python manage.py check
python manage.py runserver
```

Файл `db.sqlite3` в репозиторий не попадает (`.gitignore`), поэтому после
клонирования его создают две первые команды. Исходная база
`data/splitter.sqlite` лежит в репозитории; если изменились JSON-файлы,
сначала пересоздайте ее командой `python -m db.import_json`, а потом
снова запустите перенос.

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
pytest -v                  # тесты предметной области (ПР1–ПР3) и базы ПР7
python manage.py test      # тесты моделей, страниц, админки и форм (ПР5–ПР11)
```

Тесты проверяют создание объектов и значения атрибутов, методы и `__str__`
классов, поиск, отбор и сортировку коллекций, связь расхода с поездкой
и участниками, расчет балансов и переводов, сохранение объектов в JSON
и восстановление связей при загрузке. Тесты базы (`tests/test_database.py`)
создают временную базу, проверяют таблицы, внешние ключи и ограничения,
перенос данных из JSON, повторный импорт и выполнение всех запросов
из `sql/queries.sql`. Тесты Django-приложений работают с тестовой базой
Django, которую заполняет тот же перенос JSON → база ПР7 → база Django.
Они проверяют модели (строки, связи и обратные связи, ограничения базы,
правила удаления), перенос данных и его повтор, что каждая страница
открывается нужным шаблоном, показывает данные из базы (итоги, поиск,
сортировку, страницы списка, статистику, отбор по сумме категории),
подключает статические файлы, что имена маршрутов дают правильные адреса
и что для несуществующих номеров и адресов возвращается 404.
Тесты ПР10 проверяют адреса поездок и перенаправление со старых адресов,
статус расхода во всех итогах и расчете, методы менеджера, пересчет
`is_large` базой, страницы, действия и проверки формы в админке,
обработчик контекста и число SQL-запросов страниц (`assertNumQueries`).
Тесты ПР11 (`expenses/test_forms.py`) проверяют форму фильтра
(преобразование и ошибки параметров), добавление расхода, ошибки полей
и формы, даты вне поездки, чужих участников, дубликат и то, что
отмененный расход его не блокирует, редактирование без конфликта
с самим собой, 404, отмену (POST, 405 на GET, 404 на повтор), отказ
POST без CSRF-токена и загрузку фото чека (картинка, не картинка,
неверное расширение, большой файл).

## Проверка качества кода

```bash
flake8 . --extend-exclude=venv
```

Миграции создает сам Django, поэтому flake8 их не проверяет
(исключены в `.flake8`).

## План развития

На следующих этапах планируется:

- формы для создания поездок и участников на сайте;
- реализация пользователей, регистрации и разграничения доступа к поездкам;
- разработка REST API;
- контейнеризация приложения в Docker;
- настройка CI/CD и автоматических тестов.
