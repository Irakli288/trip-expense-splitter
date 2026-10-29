-- ==========================================================
-- Как устроена база данных сервиса для деления расходов в поездке
-- СУБД SQLite, сама база лежит в файле data/splitter.sqlite
-- ==========================================================

-- Поездки. budget может быть NULL, если бюджет не задан.
CREATE TABLE IF NOT EXISTS trips (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    start_date TEXT NOT NULL,
    end_date TEXT NOT NULL,
    budget REAL,
    CHECK (start_date <= end_date)
);

-- Участники. Каждый участник едет в одну конкретную поездку.
CREATE TABLE IF NOT EXISTS participants (
    id INTEGER PRIMARY KEY,
    trip_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    FOREIGN KEY (trip_id) REFERENCES trips(id)
);

-- Расходы. Каждый расход относится к поездке, и платит за него один участник.
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

-- Доли: на каких участников делится расход.
-- Это связь «многие ко многим» между expenses и participants.
CREATE TABLE IF NOT EXISTS expense_shares (
    expense_id INTEGER NOT NULL,
    participant_id INTEGER NOT NULL,
    PRIMARY KEY (expense_id, participant_id),
    FOREIGN KEY (expense_id) REFERENCES expenses(id),
    FOREIGN KEY (participant_id) REFERENCES participants(id)
);
