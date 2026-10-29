"""Настройка ASGI для проекта splitter.

Здесь создается объект application, через который ASGI-сервер
запускает сайт.

Подробнее: https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "splitter.settings")

application = get_asgi_application()
