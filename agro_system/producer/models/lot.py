# from django.contrib.gis.db import models as geomodels
from django.db import models
from .country_side import Countryside
from parameter.models.area import Area
from django.utils.translation import gettext_lazy as _
from parameter.models.countryside_condition import CountrysideCondition
from .staff import Staff
from .cost_center import CostCenter
from parameter.models.lot_rating import LotRating
from operation.models.activity import Activity
from weather.models.station_weather import WeatherStation


class Lot(models.Model):

    name = models.CharField(max_length=200, unique=True, verbose_name = _('name'))
    countryside = models.ForeignKey(Countryside, models.CASCADE,verbose_name = _('countryside'))
    area = models.ForeignKey(Area, models.CASCADE,verbose_name = _('area'))
    responsible = models.ForeignKey(Staff, models.CASCADE,verbose_name = _('responsible'))
    hectares = models.FloatField(default=0, verbose_name = _('hectares'))
    hectares_productive = models.FloatField(default=0, verbose_name = _('hectares productive'))
    cost_center = models.ForeignKey(CostCenter, models.CASCADE, verbose_name = _('cost center'))
    observations = models.TextField(blank=True, null=True, verbose_name = _('observatios'))
    activity = models.ManyToManyField(Activity, verbose_name = _('operations'))
    LotRating = models.ForeignKey(LotRating, models.CASCADE, verbose_name = _('lotRating'))
    last_activity = models.ForeignKey(Activity, models.CASCADE, related_name="lot_uact", blank=True, null=True, verbose_name = _('Last operation'))

    # Campos geográficos
    ubication = models.TextField(blank=True, null=True, verbose_name = _('ubication'))
    delimitation = models.TextField(blank=True, null=True, verbose_name = _('delimitation'))

    # Estacion meteorológica
    station = models.ForeignKey(WeatherStation, models.SET_NULL, blank=True, null=True, verbose_name = _('weather station'))
    
    
    def __str__(self):
        return f"{self.name}"

    class Meta:
        verbose_name = _('lot')
        verbose_name_plural = _('lots')
        ordering = ['name']

    