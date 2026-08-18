from django.contrib.gis.db import models as geomodels
from django.db import models
from .country_side import Countryside
from parameter.models.area import Area
from django.utils.translation import gettext_lazy as _
from parameter.models.countryside_condition import CountrysideCondition
from .staff import Staff
from .cost_center import CostCenter
from parameter.models.lot_rating import LotRating
from operation.models.variety import Variety
from weather.models.station_weather import WeatherStation
from weather.models.station_external import ExternalStation


class Lot(geomodels.Model):

    name                = models.CharField(max_length=200, unique=True, verbose_name=_('name'))
    countryside         = models.ForeignKey(Countryside, models.CASCADE, verbose_name=_('countryside'))
    area                = models.ForeignKey(Area, models.CASCADE, verbose_name=_('area'))
    responsible         = models.ForeignKey(Staff, models.CASCADE, verbose_name=_('responsible'))
    hectares            = models.FloatField(default=0, verbose_name=_('hectares'))
    hectares_productive = models.FloatField(default=0, verbose_name=_('hectares productive'))
    cost_center         = models.ForeignKey(CostCenter, models.CASCADE, verbose_name=_('cost center'))
    observations        = models.TextField(blank=True, null=True, verbose_name=_('observations'))
    activity            = models.ManyToManyField(Variety, verbose_name=_('varieties'))
    LotRating           = models.ForeignKey(LotRating, models.CASCADE, verbose_name=_('lotRating'))
    last_activity       = models.ForeignKey(Variety, models.CASCADE, related_name="lot_uact", blank=True, null=True, verbose_name=_('last variety'))

    # Campos geográficos
    ubication    = geomodels.PointField(srid=4326, blank=True, null=True, verbose_name=_('ubication'))
    delimitation = geomodels.PolygonField(srid=4326, blank=True, null=True, verbose_name=_('delimitation'))

    # Estaciones meteorológicas
    station          = models.ForeignKey(WeatherStation,  models.SET_NULL, blank=True, null=True, related_name='lots', verbose_name=_('weather station'))
    external_station = models.ForeignKey(ExternalStation, models.SET_NULL, blank=True, null=True, related_name='lots', verbose_name=_('external station'))

    def __str__(self):
        return f"{self.name}"

    @property
    def latitude(self):
        """Latitud extraída del PointField para llamadas a Open-Meteo."""
        return self.ubication.y if self.ubication else None

    @property
    def longitude(self):
        """Longitud extraída del PointField para llamadas a Open-Meteo."""
        return self.ubication.x if self.ubication else None

    class Meta:
        verbose_name = _('lot')
        verbose_name_plural = _('lots')
        ordering = ['name']
