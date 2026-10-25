"""Временная база SQLite для тестов Django-страниц (ПР7).

Тесты не зависят от состояния data/splitter.sqlite: перед тестами
класса база создается заново из sql/schema.sql и JSON-файлов,
а get_connection() на время тестов подключается к ней.
"""

import tempfile
from pathlib import Path
from unittest import mock

from db import import_json


class TemporaryDatabaseMixin:
    """Подменяет DB_PATH временной базой с данными из JSON."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._db_dir = tempfile.TemporaryDirectory()
        db_path = Path(cls._db_dir.name) / "test.sqlite"
        import_json.main(db_path)
        cls._db_patch = mock.patch("db.database.DB_PATH", db_path)
        cls._db_patch.start()

    @classmethod
    def tearDownClass(cls):
        cls._db_patch.stop()
        cls._db_dir.cleanup()
        super().tearDownClass()
