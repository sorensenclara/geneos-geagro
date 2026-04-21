from django.db import models
from django.utils.translation import gettext_lazy as _
from parameter.models.var_crop_technique import VarCropTechnique
from weather.models.station_weather import WeatherStation

class VariableRegister(models.Model):

    """ Modelo para representar Registro de Variables técnicas de cultivo"""

    name = models.CharField(max_length=200, unique=True, verbose_name = _('name'))
    variable = models.ForeignKey(VarCropTechnique, on_delete=models.CASCADE, verbose_name = _('variable'))
    date = models.DateField(verbose_name = _('date'))
    value = models.FloatField(verbose_name = _('value'))
    detail = models.TextField(verbose_name = _('detail'), null=True, blank=True,)
    station = models.ForeignKey(WeatherStation, on_delete=models.SET_NULL, null=True, verbose_name = _('weather station'))

    def __str__(self):
        return f"{self.variable} - {self.date}"

    class Meta:
        verbose_name = _('variable register')
        verbose_name_plural = _('variable registers')