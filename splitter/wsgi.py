"""Настройка WSGI для проекта splitter.

Здесь создается объект application, через который WSGI-сервер
запускает сайт.

Подробнее: https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "splitter.settings")

application = get_wsgi_application()
