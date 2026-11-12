"""Адреса сайта.

Список urlpatterns связывает адреса с представлениями. Подробнее:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Как добавить адрес:
Представление-функция
    1. Импортировать: from my_app import views
    2. Добавить в urlpatterns: path('', views.home, name='home')
Представление-класс
    1. Импортировать: from other_app.views import Home
    2. Добавить в urlpatterns: path('', Home.as_view(), name='home')
Адреса другого приложения
    1. Импортировать include(): from django.urls import include, path
    2. Добавить в urlpatterns: path('blog/', include('blog.urls'))
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("homepage.urls")),
    path("trips/", include("trips.urls")),
    path("expenses/", include("expenses.urls")),
]

# В режиме разработки загруженные файлы раздает сам Django.
# На настоящем сервере это делает веб-сервер (например, nginx).
if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL, document_root=settings.MEDIA_ROOT
    )

if settings.DEBUG_TOOLBAR:
    from debug_toolbar.toolbar import debug_toolbar_urls

    urlpatterns += debug_toolbar_urls()
