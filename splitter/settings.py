"""Настройки Django для проекта splitter.

Файл создан командой django-admin startproject (Django 5.2.18).

Про этот файл: https://docs.djangoproject.com/en/5.2/topics/settings/
Все настройки: https://docs.djangoproject.com/en/5.2/ref/settings/
"""

import os
import sys
from pathlib import Path

# Пути внутри проекта строим так: BASE_DIR / 'папка'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Быстрые настройки для разработки, для боевого сервера не годятся.
# Что поменять перед запуском на сервере, описано здесь:
# https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

# ВАЖНО: на настоящем сервере секретный ключ никому не показывать!
SECRET_KEY = (
    "django-insecure-srt&%v#x+oe+)=0bo+n-9-2c"
    "xn&fj(**y(mgv#n4pn#djper_i"
)

# ВАЖНО: на настоящем сервере DEBUG надо выключить!
DEBUG = True

ALLOWED_HOSTS = ["localhost", "127.0.0.1"]

# Идет ли запуск тестов: при тестах панель отладки не подключаем,
# иначе она добавляет свои запросы и мешает считать запросы страниц.
TESTING = "test" in sys.argv or "PYTEST_VERSION" in os.environ

# Панель Django Debug Toolbar показывается только при DEBUG
# и только для этих адресов (то есть на своем компьютере).
INTERNAL_IPS = ["127.0.0.1"]


# Приложения проекта

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "homepage",
    "trips",
    "expenses",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

DEBUG_TOOLBAR = DEBUG and not TESTING

if DEBUG_TOOLBAR:
    INSTALLED_APPS.append("debug_toolbar")
    # Middleware панели ставим первым, чтобы она видела всю обработку.
    MIDDLEWARE.insert(0, "debug_toolbar.middleware.DebugToolbarMiddleware")

ROOT_URLCONF = "splitter.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "splitter.context_processors.site",
            ],
        },
    },
]

WSGI_APPLICATION = "splitter.wsgi.application"


# База данных
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}


# Проверка паролей
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

PASSWORD_VALIDATION = "django.contrib.auth.password_validation."

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": PASSWORD_VALIDATION + "UserAttributeSimilarityValidator",
    },
    {
        "NAME": PASSWORD_VALIDATION + "MinimumLengthValidator",
    },
    {
        "NAME": PASSWORD_VALIDATION + "CommonPasswordValidator",
    },
    {
        "NAME": PASSWORD_VALIDATION + "NumericPasswordValidator",
    },
]


# Язык и время
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = "ru-RU"

TIME_ZONE = "Europe/Moscow"

USE_I18N = True

USE_TZ = True


# Статические файлы (CSS, JavaScript, картинки)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = "static/"

# Тип первичного ключа по умолчанию
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
