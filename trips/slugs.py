"""Адреса поездок латиницей: «Поездка в Казань» → poezdka-v-kazan."""

from django.utils.text import slugify

# Русские буквы и их запись латиницей.
RUSSIAN_TO_LATIN = {
    "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ё": "e",
    "ж": "zh", "з": "z", "и": "i", "й": "i", "к": "k", "л": "l", "м": "m",
    "н": "n", "о": "o", "п": "p", "р": "r", "с": "s", "т": "t", "у": "u",
    "ф": "f", "х": "kh", "ц": "ts", "ч": "ch", "ш": "sh", "щ": "shch",
    "ъ": "", "ы": "y", "ь": "", "э": "e", "ю": "iu", "я": "ia",
}


def make_slug(text, max_length=200):
    """Переводит название в латиницу и делает из него slug.

    Если в названии нет ни одной буквы или цифры, возвращает "trip".
    Адрес из одних цифр (поездка «2025») получает приставку trip-:
    такие адреса заняты старыми ссылками по номеру поездки.
    """
    latin = "".join(RUSSIAN_TO_LATIN.get(char, char) for char in text.lower())
    slug = slugify(latin)[:max_length].strip("-") or "trip"
    if slug.isdigit():
        slug = f"trip-{slug}"[:max_length]
    return slug


def unique_slug(queryset, text, max_length=200):
    """Slug, которого еще нет в queryset: poezdka, poezdka-2, poezdka-3…"""
    base = make_slug(text, max_length - 4)
    slug = base
    number = 2
    while queryset.filter(slug=slug).exists():
        slug = f"{base}-{number}"
        number += 1
    return slug
