from django.db import models
from .station_weather import WeatherStation
from django.utils.translation import gettext_lazy as _

class WeatherData(models.Model):

    """ Modelo para representar los datos meteorológicos registrados por las estaciones. """

    timestamp = models.DateTimeField(verbose_name= _('timestamp'))
    station = models.ForeignKey(WeatherStation, on_delete=models.SET_NULL, null=True, blank=True, verbose_name= _('weather station'))
   
    # temperatura
    temp = models.FloatField(null=True, blank=True, verbose_name= _('temperature'))
    #feels_like = models.FloatField(null=True, blank=True, verbose_name= _('feels like'))

    # humedad
    humidity = models.FloatField(null=True, blank=True, verbose_name= _('humidity'))

    # presión
    #pressure = models.FloatField(null=True, blank=True, verbose_name= _('pressure'))

    # viento
    wind_speed = models.FloatField(null=True, blank=True, verbose_name= _('wind speed'))
    wind_gust = models.FloatField(null=True, blank=True, verbose_name= _('wind gust')) # Ráfaga de viento actual windgustmph
    wind_gust_max = models.FloatField(null=True, blank=True, verbose_name= _('wind gust max')) # Ráfaga de viento máxima del día (maxdailygust)
    wind_dir = models.CharField(max_length=10, null=True, blank=True, verbose_name= _('wind direction'))

    # lluvia
    rain_rate = models.FloatField(null=True, blank=True, verbose_name= _('rain rate')) # Intensidad de lluvia (mm/h)
    rain_total = models.FloatField(null=True, blank=True, verbose_name= _('rain total'))
    rain_week = models.FloatField(null=True, blank=True, verbose_name= _('rain week')) # Lluvia acumulada semanal (mm)

    # radiación
    #uv = models.FloatField(null=True, blank=True, verbose_name= _('uv'))
    solar_radiation = models.FloatField(null=True, blank=True, verbose_name= _('solar radiation'))

    # raw payload (debug)
    raw_data = models.JSONField(null=True, blank=True, verbose_name= _('raw data'))

    def __str__(self):
        return f"{self.timestamp} - {self.temp}°C"
    
    class Meta:
        verbose_name = _('weather data')
        verbose_name_plural = _('weather data')