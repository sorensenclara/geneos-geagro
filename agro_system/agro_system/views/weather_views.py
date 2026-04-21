from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from weather.models import WeatherData

@login_required
def WeatherView(request):
    
    weather = WeatherData.objects.last()  # Obtener el último registro de datos meteorológicos
    data = {
        'temp': weather.temp,
        'humidity': weather.humidity,
        'wind_speed': weather.wind_speed,
        'wind_gust': weather.wind_gust,
        'wind_dir': weather.wind_dir,
        'rain_rate': weather.rain_rate,
        'rain_total': weather.rain_total,
        'weather_data': weather
    }

    return render(request, 'pages/weather.html', data)