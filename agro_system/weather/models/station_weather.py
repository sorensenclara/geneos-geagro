from django.db import models
from django.utils.translation import gettext_lazy as _


class WeatherStation(models.Model):

    """ Modelo para representar una estación meteorológica en el sistema. """

    INTERVAL_CHOICES = [
        (1,   _('1 minute')),
        (5,   _('5 minutes')),
        (15,  _('15 minutes')),
        (30,  _('30 minutes')),
        (60,  _('1 hour')),
        (120, _('2 hours')),
    ]

    name = models.CharField(max_length=100, verbose_name=_('name'))
    passkey = models.CharField(unique=True, max_length=100, verbose_name=_('passkey'))
    latitude = models.FloatField(verbose_name=_('latitude'))
    longitude = models.FloatField(verbose_name=_('longitude'))
    save_interval = models.PositiveIntegerField(
        choices=INTERVAL_CHOICES,
        default=15,
        verbose_name=_('save interval (minutes)'),
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _('weather station')
        verbose_name_plural = _('weather stations')