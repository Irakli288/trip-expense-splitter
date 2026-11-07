"""Тестовые данные для Django-тестов.

Перед тестами класса данные проходят тот же путь, что и настоящие:
JSON → временная база SQLite (как в ПР7) → тестовая база Django
через скрипт переноса import_sqlite_to_orm. Так тесты заодно
проверяют, что перенос не теряет записи и связи.
"""

import tempfile
from pathlib import Path

from db import import_json, import_sqlite_to_orm


class ProjectDataMixin:
    """Заполняет тестовую базу Django данными проекта из JSON."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        with tempfile.TemporaryDirectory() as folder:
            source_db = Path(folder) / "source.sqlite"
            import_json.main(source_db)
            import_sqlite_to_orm.transfer(source_db)
