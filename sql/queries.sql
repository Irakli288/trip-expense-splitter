-- ==========================================================
-- Все SQL-запросы сервиса для деления расходов в поездке
-- Проверить можно так: sqlite3 data/splitter.sqlite
--
-- Эти запросы выполняют Django-представления. Значения из адреса
-- или формы там передаются через знаки ?, а здесь вместо них
-- подставлены обычные значения, чтобы запрос можно было запустить.
-- ==========================================================


-- ----------------------------------------------------------
-- Просто списки
-- ----------------------------------------------------------

-- Запрос 1. Все поездки по дате начала
-- (выпадающий список поездок в поиске расходов, /expenses/).
SELECT
    id,
    name
FROM trips
ORDER BY start_date;

-- Запрос 2. Участники поездки по алфавиту
-- (страница поездки /trips/1/ и расчет /trips/1/settlement/).
-- В представлении вместо 1 стоит ?: WHERE trip_id = ?
SELECT
    id,
    name
FROM participants
WHERE trip_id = 1
ORDER BY name;

-- Запрос 3. Три самых дорогих расхода (/expenses/statistics/).
SELECT
    expenses.id,
    expenses.title,
    expenses.amount,
    trips.name AS trip_name
FROM expenses
JOIN trips
    ON expenses.trip_id = trips.id
ORDER BY expenses.amount DESC
LIMIT 3;


-- ----------------------------------------------------------
-- Поиск и фильтры (WHERE)
-- ----------------------------------------------------------

-- Запрос 4. Ищем расходы по поездке, категории и минимальной сумме
-- (/expenses/?trip=1&category=транспорт&min_amount=5000).
-- Часть (? = 0 OR ...) выключает фильтр, если поездка не выбрана,
-- а (? = '' OR ...) делает то же, если не выбрана категория.
-- Параметры в представлении: [trip_id, trip_id, category, category, min_amount]
SELECT
    expenses.id,
    strftime('%d.%m.%Y', expenses.expense_date) AS expense_date_ru,
    expenses.title,
    expenses.category,
    expenses.amount,
    trips.id AS trip_id,
    trips.name AS trip_name,
    participants.name AS payer_name
FROM expenses
JOIN trips
    ON expenses.trip_id = trips.id
JOIN participants
    ON expenses.payer_id = participants.id
WHERE (1 = 0 OR expenses.trip_id = 1)
    AND ('транспорт' = '' OR expenses.category = 'транспорт')
    AND expenses.amount >= 5000
ORDER BY expenses.expense_date, expenses.id;

-- Запрос 5. Сколько расходов нашлось и на какую сумму
-- (итог под таблицей на /expenses/, условия те же, что в запросе 4).
SELECT
    COUNT(*) AS expenses_count,
    COALESCE(SUM(amount), 0) AS expenses_total
FROM expenses
WHERE (0 = 0 OR trip_id = 0)
    AND ('' = '' OR category = '')
    AND amount >= 0;

-- Запрос 6. Участники поездки, которые пока ни за что не платили
-- (подзапрос NOT IN, страница поездки /trips/2/).
-- Параметры в представлении: [trip_id, trip_id]
SELECT
    id,
    name
FROM participants
WHERE trip_id = 2
    AND id NOT IN (
        SELECT payer_id
        FROM expenses
        WHERE trip_id = 2
    )
ORDER BY name;


-- ----------------------------------------------------------
-- Данные сразу из нескольких таблиц (JOIN)
-- ----------------------------------------------------------

-- Запрос 7. Расходы поездки и кто за них платил
-- (страница поездки /trips/1/ и расчет /trips/1/settlement/).
-- В представлении: WHERE expenses.trip_id = ?
SELECT
    expenses.id,
    expenses.title,
    expenses.amount,
    expenses.category,
    expenses.expense_date,
    strftime('%d.%m.%Y', expenses.expense_date) AS expense_date_ru,
    expenses.payer_id,
    participants.name AS payer_name
FROM expenses
JOIN participants
    ON expenses.payer_id = participants.id
WHERE expenses.trip_id = 1
ORDER BY expenses.expense_date, expenses.id;

-- Запрос 8. Расход по номеру вместе с поездкой и плательщиком
-- (страница расхода /expenses/1/). В представлении: WHERE expenses.id = ?
SELECT
    expenses.id,
    expenses.title,
    expenses.amount,
    expenses.category,
    strftime('%d.%m.%Y', expenses.expense_date) AS expense_date_ru,
    trips.id AS trip_id,
    trips.name AS trip_name,
    participants.name AS payer_name
FROM expenses
JOIN trips
    ON expenses.trip_id = trips.id
JOIN participants
    ON expenses.payer_id = participants.id
WHERE expenses.id = 1;

-- Запрос 9. На кого делится расход
-- (страница расхода /expenses/1/). В представлении: WHERE ... = ?
SELECT
    participants.id,
    participants.name
FROM expense_shares
JOIN participants
    ON expense_shares.participant_id = participants.id
WHERE expense_shares.expense_id = 1
ORDER BY participants.id;

-- Запрос 10. Доли по всем расходам поездки
-- (кто в каком расходе участвует, нужно для расчета /trips/1/settlement/).
-- В представлении: WHERE expenses.trip_id = ?
SELECT
    expense_shares.expense_id,
    expense_shares.participant_id
FROM expense_shares
JOIN expenses
    ON expense_shares.expense_id = expenses.id
WHERE expenses.trip_id = 1
ORDER BY expense_shares.expense_id, expense_shares.participant_id;


-- ----------------------------------------------------------
-- Подсчеты: COUNT, SUM, MAX и другие
-- ----------------------------------------------------------

-- Запрос 11. Общие цифры для главной страницы (/):
-- сколько поездок, участников и расходов, сколько потрачено всего и самый дорогой расход.
SELECT
    (SELECT COUNT(*) FROM trips) AS trips_count,
    (SELECT COUNT(*) FROM participants) AS participants_count,
    COUNT(*) AS expenses_count,
    COALESCE(SUM(amount), 0) AS expenses_total,
    MAX(amount) AS max_amount
FROM expenses;


-- ----------------------------------------------------------
-- Группировка (GROUP BY) и отбор групп (HAVING)
-- ----------------------------------------------------------

-- Запрос 12. Поездки с числом участников, суммой расходов
-- и тем, сколько потрачено от бюджета (список поездок /trips/).
-- LEFT JOIN нужен, чтобы поездки без расходов тоже попали в список (с суммой 0).
SELECT
    trips.id,
    trips.name,
    strftime('%d.%m.%Y', trips.start_date) AS start_date_ru,
    strftime('%d.%m.%Y', trips.end_date) AS end_date_ru,
    CAST(julianday(trips.end_date) - julianday(trips.start_date)
         AS INTEGER) + 1 AS duration,
    trips.budget,
    (SELECT COUNT(*)
     FROM participants
     WHERE participants.trip_id = trips.id) AS participants_count,
    COUNT(expenses.id) AS expenses_count,
    COALESCE(SUM(expenses.amount), 0) AS total,
    CASE
        WHEN trips.budget IS NULL THEN 'none'
        WHEN COALESCE(SUM(expenses.amount), 0) > trips.budget THEN 'over'
        WHEN COALESCE(SUM(expenses.amount), 0) >= trips.budget * 0.8
            THEN 'warning'
        ELSE 'ok'
    END AS budget_level
FROM trips
LEFT JOIN expenses
    ON expenses.trip_id = trips.id
GROUP BY trips.id
ORDER BY trips.start_date;

-- Запрос 13. Одна поездка с итогами и состоянием бюджета
-- (страница поездки /trips/1/). В представлении: WHERE trips.id = ?
SELECT
    trips.id,
    trips.name,
    strftime('%d.%m.%Y', trips.start_date) AS start_date_ru,
    strftime('%d.%m.%Y', trips.end_date) AS end_date_ru,
    CAST(julianday(trips.end_date) - julianday(trips.start_date)
         AS INTEGER) + 1 AS duration,
    trips.budget,
    COALESCE(SUM(expenses.amount), 0) AS total,
    CAST(COALESCE(SUM(expenses.amount), 0) * 100 / trips.budget
         AS INTEGER) AS used_percent,
    ABS(trips.budget - COALESCE(SUM(expenses.amount), 0)) AS budget_diff,
    CASE
        WHEN trips.budget IS NULL THEN 'none'
        WHEN COALESCE(SUM(expenses.amount), 0) > trips.budget THEN 'over'
        WHEN COALESCE(SUM(expenses.amount), 0) >= trips.budget * 0.8
            THEN 'warning'
        ELSE 'ok'
    END AS budget_level
FROM trips
LEFT JOIN expenses
    ON expenses.trip_id = trips.id
WHERE trips.id = 1
GROUP BY trips.id;

-- Запрос 14. Сколько потрачено по каждой категории (/expenses/statistics/).
SELECT
    category,
    COUNT(*) AS expenses_count,
    SUM(amount) AS total,
    ROUND(AVG(amount), 2) AS average_amount,
    MAX(amount) AS max_amount
FROM expenses
GROUP BY category
ORDER BY total DESC;

-- Запрос 15. Сколько заплатил каждый участник (/expenses/statistics/).
-- Кто ни за что не платил, тоже есть в списке, с суммой 0.
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

-- Запрос 16. Категории, где потрачено не меньше заданной суммы
-- (/expenses/statistics/?min_total=5000). В представлении: HAVING ... >= ?
SELECT
    category,
    SUM(amount) AS total
FROM expenses
GROUP BY category
HAVING SUM(amount) >= 5000
ORDER BY total DESC;

-- Запрос 17. Поездки, где потрачено 80% бюджета и больше
-- (/expenses/statistics/).
SELECT
    trips.id,
    trips.name,
    trips.budget,
    SUM(expenses.amount) AS total,
    CAST(SUM(expenses.amount) * 100 / trips.budget AS INTEGER)
        AS used_percent
FROM trips
JOIN expenses
    ON expenses.trip_id = trips.id
WHERE trips.budget IS NOT NULL
GROUP BY trips.id
HAVING SUM(expenses.amount) >= trips.budget * 0.8
ORDER BY used_percent DESC;
