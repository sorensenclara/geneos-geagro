from django.db import models

# models.py
from django.db import models

class WeatherData(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)

    # temperatura
    temp = models.FloatField(null=True, blank=True)
    feels_like = models.FloatField(null=True, blank=True)

    # humedad
    humidity = models.FloatField(null=True, blank=True)

    # presión
    pressure = models.FloatField(null=True, blank=True)

    # viento
    wind_speed = models.FloatField(null=True, blank=True)
    wind_gust = models.FloatField(null=True, blank=True)
    wind_dir = models.FloatField(null=True, blank=True)

    # lluvia
    rain_rate = models.FloatField(null=True, blank=True)
    rain_total = models.FloatField(null=True, blank=True)

    # radiación
    uv = models.FloatField(null=True, blank=True)
    solar_radiation = models.FloatField(null=True, blank=True)

    # raw payload (debug)
    raw_data = models.JSONField(null=True, blank=True)

    def __str__(self):
        return f"{self.timestamp} - {self.temp}°C"