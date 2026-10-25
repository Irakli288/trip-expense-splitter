from django.http import HttpResponse


def trips(request):
    return HttpResponse("Список поездок")


def trip_detail(request, trip_id):
    return HttpResponse(f"Поездка {trip_id}")


def trip_settlement(request, trip_id):
    return HttpResponse(f"Расчет по поездке {trip_id}")
