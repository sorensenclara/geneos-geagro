from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator
from django.utils.translation import gettext_lazy as _


class ExternalStation(models.Model):

    """ Modelo para representar una estación meteorológica externar (por API) en el sistema. """

    name = models.CharField(max_length=100, verbose_name=_('name'))
    latitude = models.FloatField(verbose_name=_('latitude'))
    longitude = models.FloatField(verbose_name=_('longitude'))
    forecast_days = models.PositiveIntegerField(
        verbose_name=_('forecast days'),
        default=7,
        validators=[MinValueValidator(1), MaxValueValidator(16)],
        help_text=_('Number of days to forecast (Per default, only 7 days are returned. Up to 16 days of forecast are possible)'),
    )
    variable = models.CharField(max_length=100, verbose_name=_('variable'), help_text=_('Variable to be retrieved from the external station (e.g., temperature, humidity, etc.)'))  
    url = models.URLField(verbose_name=_('url'), help_text=_('URL of the external station API endpoint'))
    
    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _('weather station external')
        verbose_name_plural = _('weather stations external')