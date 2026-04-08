from django.shortcuts import render
# views.py
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import WeatherData


def to_float(val):
    try:
        return float(val)
    except:
        return None
    

# TODO AGREGAR UNA CLAVE SECRETA PARA AUTENTICAR EL INGESTO DE DATOS DESDE LA ESTACIÓN METEOROLÓGICA
API_KEY = "mi_clave_secreta"

def f_to_c(f):
     # Convierte Fahrenheit a Celsius
    return round((f - 32) * 5.0 / 9.0, 2) if f is not None else None

@csrf_exempt
def weather_ingest(request):

    # Descomentar cuando se agregue la clave secreta 
    # if request.GET.get("key") != API_KEY:
    #     return JsonResponse({"error": "unauthorized"}, status=403)
     
    data = request.POST.dict()
    temp_f = to_float(data.get("tempf") or data.get("indoortempf"))

    WeatherData.objects.create(
        temp=f_to_c(temp_f),
        humidity=to_float(data.get("humidity") or data.get("indoorhumidity")),
        pressure=to_float(data.get("baromrelin")),
        wind_speed=to_float(data.get("windspeedmph")),
        wind_gust=to_float(data.get("windgustmph")),
        wind_dir=to_float(data.get("winddir")),
        rain_rate=to_float(data.get("rainratein")),
        rain_total=to_float(data.get("dailyrainin")),
        uv=to_float(data.get("uv")),
        solar_radiation=to_float(data.get("solarradiation")),
        raw_data=data
    )

    return JsonResponse({"status": "ok"})