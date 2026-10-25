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
из JSON в базу SQLite: страницы сайта получают их SQL-запросами.

## Используемые технологии

- Python 3;
- Django 5.2 — веб-фреймворк;
- Django Template Language — шаблоны страниц;
- HTML5 — разметка веб-страниц;
- CSS3 и Bootstrap 5.3 (подключается через CDN) — оформление страниц;
- JavaScript — небольшое поведение интерфейса;
- SQLite и модуль `sqlite3` стандартной библиотеки — база данных (ПР7);
- SQL — выборка и обработка данных;
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
- перенос данных из JSON в базу SQLite и работа веб-страниц с базой (ПР7);
- поиск расходов по поездке, категории и минимальной сумме;
- статистика: итоги по категориям, кто сколько оплатил, крупные категории,
  поездки с почти исчерпанным бюджетом;
- обработка некорректного ввода и ошибок файлов без аварийного завершения.

## Веб-интерфейс (ПР5–ПР6)

Django добавлен к существующему проекту: `manage.py` лежит в корне
репозитория рядом с `main.py`, а код ПР3 (пакет `models`, `storage.py`,
JSON-файлы, тесты, консольное меню) сохранен и продолжает работать.
До ПР7 страницы строились по объектам `Trip`, `Participant`, `Expense`
и `Settlement`, которые `storage.py` загружал из JSON. С ПР7 страницы
получают данные из базы SQLite (раздел «База данных SQLite (ПР7)»).
Django ORM и Django-модели пока не используются, формы еще не реализованы.

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
| `/expenses/statistics/` | `expenses:statistics` | `expenses.views.statistics` | `expenses/statistics.html` |
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
  подключается в цикле `{% for trip in trips %}` и получает строку
  результата SQL-запроса как переменную `trip`;
- `trips/includes/budget_badge.html` — цветная отметка бюджета
  (в списке поездок и на странице поездки);
- `expenses/includes/category_badge.html` — категория расхода
  (в списке расходов, на странице расхода, в таблице расходов поездки);
  на странице статистики подключается с параметром:
  `{% include "expenses/includes/category_badge.html" with expense=item %}`.

**Контекст.** View-функции передают данные словарем контекста, например
в `trips.views.trips` (ПР7):

```python
trips_data = conn.execute(TRIPS_QUERY).fetchall()   # строки sqlite3.Row
return render(request, "trips/trip_list.html", {"trips": trips_data})
```

В шаблоне к полям строки результата обращаются по имени столбца через
точку: `{{ trip.name }}`, `{{ trip.total }}`, `{{ expense.payer_name }}`.

**Циклы и условия.** Списки выводятся циклом `{% for %}`, пустая
коллекция обрабатывается веткой `{% empty %}` («Поездок пока нет»,
«Участников нет», «Расходы не найдены.», «Переводы не нужны»). Переводы
расчета перебираются с распаковкой кортежа:
`{% for debtor, creditor, amount in transfers %}`. Условия `{% if %}`
выбирают цвет отметки бюджета по `budget_level`, цвет баланса участника
(`row.balance > 0`, `< 0`, `= 0`) и ветку «объект не найден».

Уровень расходования бюджета — `none`, `ok`, `warning` (80% и больше)
или `over`. В ПР6 его вычислял метод `Trip.budget_level(total)`, с ПР7
для страниц сайта то же правило записано в SQL-запросе выражением
`CASE ... END AS budget_level`; шаблон только выбирает по уровню CSS-класс.

### Фильтры шаблонов

Фильтры применяются для представления данных и не содержат бизнес-логику:

| Фильтр | Где | Что делает |
|---|---|---|
| `length` | `{{ trips\|length }}`, `{{ participants\|length }}`, `{{ expenses\|length }}` | количество поездок, участников, расходов |
| `default` | `{{ trip.name\|default:"Без названия" }}` | значение, если название пустое |
| `date` | в ПР6 `{{ trip.start_date\|date:"d.m.Y" }}`; с ПР7 дату форматирует SQL: `strftime('%d.%m.%Y', start_date)` | дата в формате 03.11.2026 |
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
перенесены в SQL-запросы (см. раздел «База данных SQLite (ПР7)»).
Расчет «кто кому должен» по-прежнему выполняет класс `Settlement`:
view-функция `trip_settlement` строит объекты `Trip`, `Participant`
и `Expense` из строк SQLite и вызывает `get_balances()` и
`get_transfers()`.

Отложены до появления форм и POST-запросов: создание поездки, добавление
участника, добавление и удаление расхода. Эти операции по-прежнему
доступны в консольной версии.

## База данных SQLite (ПР7)

Данные проекта перенесены из JSON-файлов в базу SQLite
`data/splitter.sqlite`. Работа с базой выполняется модулем `sqlite3`
стандартной библиотеки Python, без Django ORM.

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

| № | Запрос | Элементы SQL | Где используется |
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

### Получение данных в Django-представлениях

Каждая view-функция открывает соединение через `get_connection()`,
настраивает `conn.row_factory = sqlite3.Row`, выполняет запрос и передает
результат в шаблон через контекст. Благодаря `sqlite3.Row` к полям
обращаются по имени: `row["total"]` в Python и `{{ trip.total }}`
в шаблоне.

```python
def trip_detail(request, trip_id):
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    try:
        trip = conn.execute(TRIP_QUERY, [trip_id]).fetchone()
        ...
    finally:
        conn.close()
```

Значения из URL и формы (номер поездки, категория, сумма) передаются
только параметрами `?`, например
`conn.execute(EXPENSES_QUERY, [trip_id, trip_id, category, category, min_amount])`.
Конкатенация строк и f-строки для подстановки значений в SQL
не используются. Некорректные значения параметров (`?trip=abc`,
отрицательная сумма, неизвестная категория) заменяются значениями
по умолчанию.

### Страницы с данными из SQLite

| Страница | Что показывает | Запросы |
|---|---|---|
| Главная `/` | сводка: поездки, участники, расходы, сумма | 11 |
| Поездки `/trips/` | карточки поездок с итогами и отметкой бюджета | 12 |
| Поездка `/trips/<id>/` | бюджет, участники, расходы, кто еще не платил | 2, 6, 7, 13 |
| Расчет `/trips/<id>/settlement/` | балансы и переводы (класс `Settlement`) | 2, 7, 10 |
| Расходы `/expenses/` | поиск по поездке, категории и сумме, итог | 1, 4, 5 |
| Расход `/expenses/<id>/` | плательщик, участники, доля каждого | 8, 9 |
| Статистика `/expenses/statistics/` | категории, плательщики, крупные расходы и категории, бюджет | 3, 14–17 |

Навигация: Главная | Поездки | Расходы | Статистика. Все ссылки
строятся тегом `{% url %}`; SQL-запросы в интерфейсе не показываются.

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
├── db/                     # слой базы данных SQLite (ПР7)
│   ├── __init__.py
│   ├── database.py         # подключение к базе
│   ├── import_json.py      # перенос данных из JSON в базу
│   └── testing.py          # временная база для тестов страниц
├── sql/
│   ├── schema.sql          # создание таблиц
│   └── queries.sql         # SQL-запросы проекта
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
│   │   ├── statistics.html
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
│   ├── expenses.json
│   └── splitter.sqlite     # база данных SQLite (ПР7)
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
python -m db.import_json      # создать базу SQLite и перенести данные JSON
python manage.py migrate      # служебные таблицы Django, один раз
python manage.py check
python manage.py runserver
```

База `data/splitter.sqlite` уже лежит в репозитории; `python -m db.import_json`
нужен, чтобы пересоздать ее данные после изменения JSON-файлов.

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
pytest -v                  # тесты предметной области (ПР1–ПР3) и базы (ПР7)
python manage.py test      # тесты веб-страниц (ПР5–ПР7)
```

Тесты проверяют создание объектов и значения атрибутов, методы и `__str__`
классов, поиск, отбор и сортировку коллекций, связь расхода с поездкой
и участниками, расчет балансов и переводов, сохранение объектов в JSON
и восстановление связей при загрузке. Тесты базы (`tests/test_database.py`)
создают временную базу, проверяют таблицы, внешние ключи и ограничения,
перенос данных из JSON, повторный импорт и выполнение всех запросов
из `sql/queries.sql`. Тесты Django-приложений работают с временной базой
SQLite и проверяют, что каждая страница открывается нужным шаблоном,
показывает данные из базы (итоги, поиск, статистику, HAVING с параметром),
подключает статические файлы, что имена маршрутов дают правильные адреса
и что для несуществующих номеров и адресов возвращается 404.

## Проверка качества кода

```bash
flake8 . --extend-exclude=venv
```

## План развития

На следующих этапах планируется:

- подключение базы данных к Django через Django ORM: модели `Trip`,
  `Participant`, `Expense`, миграции и административная панель;
- формы Django для создания поездок, участников и расходов;
- реализация пользователей, регистрации и разграничения доступа к поездкам;
- разработка REST API;
- контейнеризация приложения в Docker;
- настройка CI/CD и автоматических тестов.
