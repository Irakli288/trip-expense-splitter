from django.urls import path

from . import views

app_name = "trips"

urlpatterns = [
    path("", views.trips, name="list"),
    # Старый адрес по номеру поездки оставлен, чтобы не ломать ссылки.
    path("<int:trip_id>/", views.trip_by_id, name="by_id"),
    path("<slug:slug>/", views.trip_detail, name="detail"),
    path(
        "<slug:slug>/settlement/",
        views.trip_settlement,
        name="settlement",
    ),
]
