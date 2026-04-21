from django.db import models
from django.utils.translation import gettext_lazy as _
class WeatherStation(models.Model):

    """ Modelo para representar una estación meteorológica en el sistema. """

    name = models.CharField(max_length=100, verbose_name = _('name'))
    passkey = models.CharField(unique=True, max_length=100, verbose_name = _('passkey'))
    latitude = models.FloatField(verbose_name= _('latitude'))
    longitude = models.FloatField(verbose_name= _('longitude'))

    def __str__(self):
        return self.name + self.lot.name if self.lot else ""

    class Meta:
        verbose_name = _('weather station')
        verbose_name_plural = _('weather stations')