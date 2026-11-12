"""Свои проверки значений полей расхода.

Валидатор — обычная функция: получает значение и, если оно не подходит,
вызывает ValidationError. Django вызывает его при проверке формы.
"""

from django.core.exceptions import ValidationError

# Самый большой файл чека, который можно загрузить.
MAX_RECEIPT_SIZE_MB = 5


def validate_title_has_letters(value):
    """Название расхода должно содержать хотя бы одну букву.

    Названия вроде «123» или «---» ничего не говорят о том,
    на что потрачены деньги.
    """
    if not any(char.isalpha() for char in value):
        raise ValidationError(
            "Название должно содержать хотя бы одну букву.",
            code="no_letters",
        )


def validate_receipt_size(file):
    """Фото чека не больше MAX_RECEIPT_SIZE_MB мегабайт."""
    if file.size > MAX_RECEIPT_SIZE_MB * 1024 * 1024:
        raise ValidationError(
            f"Файл больше {MAX_RECEIPT_SIZE_MB} МБ, выберите фото поменьше.",
            code="too_big",
        )
