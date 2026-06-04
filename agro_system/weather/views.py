from django.shortcuts import render
# views.py
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import WeatherData
from datetime import datetime, timezone as dt_timezone, timedelta
from .models.station_weather import WeatherStation


def to_float(val):
    try:
        return float(val)
    except:
        return None


def in_to_mm(i):
    # Convierte pulgadas a milímetros
    return round(i * 25.4, 2) if i is not None else None


# TODO AGREGAR UNA CLAVE SECRETA PARA AUTENTICAR EL INGESTO DE DATOS DESDE LA ESTACIÓN METEOROLÓGICA
API_KEY = "mi_clave_secreta"

def f_to_c(f):
     # Convierte Fahrenheit a Celsius
    return round((f - 32) * 5.0 / 9.0, 2) if f is not None else None

def deg_to_cardinal(deg):
    """ Convierte grados a dirección cardinal"""
    if deg is None:
        return None

    dirs = ["N", "NE", "E", "SE", "S", "SO", "O", "NO"]
    ix = round(deg / 45) % 8
    return dirs[ix]

@csrf_exempt
def weather_ingest(request):

    # Descomentar cuando se agregue la clave secreta 
    # if request.GET.get("key") != API_KEY:
    #     return JsonResponse({"error": "unauthorized"}, status=403)
    
    # TODO La estacion manda un POST, si se prueba con url hay que cambiar a GET
    data = request.POST.dict()
    temp_f = to_float(data.get("tempf") if data.get("tempf") else data.get("tempinf"))
    widn_dir_deg = to_float(data.get("winddir"))
    # data["winddir"] = deg_to_cardinal(widn_dir_deg)
    winddir = deg_to_cardinal(widn_dir_deg)
    date_str = data.get("dateutc")

    if date_str:
        timestamp = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
        timestamp = timestamp.replace(tzinfo=dt_timezone.utc)
    else:
        timestamp = dt_timezone.now()

    passkey = data.get("PASSKEY")

    station = WeatherStation.objects.get(passkey=passkey)
    rain_total = in_to_mm(to_float(data.get("dailyrainin")))
    rain_rate = in_to_mm(to_float(data.get("rainratein"))) 
    rain_week = in_to_mm(to_float(data.get("weeklyrainin"))) 
    rain_month = in_to_mm(to_float(data.get("monthlyrainin")))
    rain_year = in_to_mm(to_float(data.get("yearlyrainin")))

    if not station:
        return JsonResponse({"error": "Estación no encontrada"}, status=404)

    last = WeatherData.objects.filter(station=station).order_by('-timestamp').first()
    if last and (timestamp - last.timestamp) < timedelta(minutes=station.save_interval):
        return JsonResponse({"status": "skipped"})

    WeatherData.objects.create(
        station=station,
        timestamp=timestamp,
        temp=f_to_c(temp_f),
        humidity=to_float(data.get("humidity") or data.get("humidityin")),
        #pressure=to_float(data.get("baromrelin")),
        wind_speed=to_float(data.get("windspeedmph")),
        wind_gust=to_float(data.get("windgustmph")),
        wind_gust_max=to_float(data.get("maxdailygust")),
        wind_dir=winddir,
        rain_rate=rain_rate,
        rain_total= rain_total,
        rain_week=rain_week,
        rain_month=rain_month,
        rain_year=rain_year,
        #uv=to_float(data.get("uv")),
        solar_radiation=to_float(data.get("solarradiation")),
        raw_data=data
    )


    return JsonResponse({"status": "ok"})