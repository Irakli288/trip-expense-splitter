-- ==========================================================
-- Сервис распределения расходов поездки: структура базы данных
-- ПР7. СУБД SQLite, файл базы: data/splitter.sqlite
-- ==========================================================

-- Поездки. budget может быть NULL: бюджет поездки не задан.
CREATE TABLE IF NOT EXISTS trips (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    start_date TEXT NOT NULL,
    end_date TEXT NOT NULL,
    budget REAL,
    CHECK (start_date <= end_date)
);

-- Участники. Каждый участник относится к одной поездке.
CREATE TABLE IF NOT EXISTS participants (
    id INTEGER PRIMARY KEY,
    trip_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    FOREIGN KEY (trip_id) REFERENCES trips(id)
);

-- Расходы. Расход относится к поездке и оплачен одним участником.
CREATE TABLE IF NOT EXISTS expenses (
    id INTEGER PRIMARY KEY,
    trip_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    amount REAL NOT NULL CHECK (amount > 0),
    category TEXT NOT NULL DEFAULT 'прочее'
        CHECK (category IN ('жилье', 'транспорт', 'еда',
                            'развлечения', 'прочее')),
    expense_date TEXT NOT NULL,
    payer_id INTEGER NOT NULL,
    FOREIGN KEY (trip_id) REFERENCES trips(id),
    FOREIGN KEY (payer_id) REFERENCES participants(id)
);

-- Доли расходов: между какими участниками делится расход.
-- Связь «многие ко многим» между expenses и participants.
CREATE TABLE IF NOT EXISTS expense_shares (
    expense_id INTEGER NOT NULL,
    participant_id INTEGER NOT NULL,
    PRIMARY KEY (expense_id, participant_id),
    FOREIGN KEY (expense_id) REFERENCES expenses(id),
    FOREIGN KEY (participant_id) REFERENCES participants(id)
);
