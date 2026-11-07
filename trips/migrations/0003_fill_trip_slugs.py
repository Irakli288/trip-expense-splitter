"""Заполняет адрес (slug) у поездок, которые были созданы до его появления."""

from django.db import migrations

from trips.slugs import unique_slug


def fill_slugs(apps, schema_editor):
    Trip = apps.get_model("trips", "Trip")
    for trip in Trip.objects.filter(slug__isnull=True).order_by("pk"):
        others = Trip.objects.exclude(pk=trip.pk)
        trip.slug = unique_slug(others, trip.name)
        trip.save(update_fields=["slug"])


class Migration(migrations.Migration):

    dependencies = [
        ("trips", "0002_trip_slug_and_help_texts"),
    ]

    # Обратно ничего делать не нужно: поле slug удалит миграция 0002.
    operations = [
        migrations.RunPython(fill_slugs, migrations.RunPython.noop),
    ]
