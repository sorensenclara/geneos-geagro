from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
from user.admin.adminSite import adminSite
from agro_system.utils.bcr import get_quotes_bcr
from producer.models.lot import Lot
import requests


# TODO esto no se esta usando, es la vista del dashboard del admin
@staff_member_required
def custom_admin_dashboard(request):

    # Recorrer los lotes e imprimir latitud y longitud
    lotes = Lot.objects.all()
    for lote in lotes:
        if lote.ubication:
            print(f"Lote: {lote.name} - Latitud: {lote.ubication.y}, Longitud: {lote.ubication.x}")

    precios = get_quotes_bcr()
    context = adminSite.each_context(request)
    context['precios'] = precios
    data = []
    url = "https://ws.smn.gob.ar/map_items/weather"
    try:
        response = requests.get(url, timeout=5)
        data = response.json()
    except Exception:
        data = []
    context['clima'] = data
    print ("Datos climáticos obtenidos:", data)

    # Obtener pronóstico del clima para una ubicación específica
    location_id = "609de837818e15902c75354a"  # Reemplazar con el ID de ubicación deseado
    forecast_url = f"https://ws.smn.gob.ar/v1/forecast/location/609de837818e15902c75354a"
    try:
        forecast_response = requests.get(forecast_url, timeout=5)
        context['clima_forecast'] = forecast_response.json()
    except Exception:
        context['clima_forecast'] = []
    # print("Pronóstico del clima obtenido:", context['clima_forecast'])

    return render(request, 'admin/custom_dashboard.html', context)