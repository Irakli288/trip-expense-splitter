"""Поиск по тексту без учета регистра для страниц сайта."""

from django.db.models import Q


def text_search(query, *fields):
    """Условие «query встречается хотя бы в одном из полей».

    SQLite сравнивает без учета регистра только латиницу, поэтому
    «казань» сам по себе не найдет «Казань». Чтобы поиск работал
    по-русски, ищем запрос как есть, строчными буквами и с заглавной
    первой буквой. Условия для всех полей объединяются через ИЛИ (|).
    """
    variants = {query, query.lower(), query.capitalize()}
    condition = Q()
    for field in fields:
        for text in variants:
            condition |= Q(**{f"{field}__icontains": text})
    return condition
