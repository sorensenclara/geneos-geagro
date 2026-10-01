from django.contrib.gis.db import models as geomodels
from django.db import models
from django.core.exceptions import ValidationError
from .country_side import Countryside
from parameter.models.area import Area
from django.utils.translation import gettext_lazy as _
from parameter.models.countryside_condition import CountrysideCondition
from .staff import Staff
from .cost_center import CostCenter
from parameter.models.lot_rating import LotRating
from operation.models.variety import Variety
from weather.models.station_weather import WeatherStation


class Lot(geomodels.Model):

    name = models.CharField(max_length=200, unique=True, verbose_name = _('name'))
    countryside = models.ForeignKey(Countryside, models.CASCADE,verbose_name = _('countryside'))
    area = models.ForeignKey(Area, models.CASCADE,verbose_name = _('area'))
    responsible = models.ForeignKey(Staff, models.CASCADE,verbose_name = _('responsible'))
    hectares = models.FloatField(default=0, verbose_name = _('hectares'))
    hectares_productive = models.FloatField(default=0, verbose_name = _('hectares productive'))
    cost_center = models.ForeignKey(CostCenter, models.CASCADE, blank=True, verbose_name = _('cost center'))
    observations = models.TextField(blank=True, null=True, verbose_name = _('observatios'))
    variety = models.ManyToManyField(Variety, verbose_name = _('varieties'))
    LotRating = models.ForeignKey(LotRating, models.CASCADE, verbose_name = _('lotRating'))
    last_variety = models.ForeignKey(Variety, models.CASCADE, related_name="lot_uact", blank=True, null=True, verbose_name = _('last variety'))

    # Campos geográficos
    ubication = geomodels.PointField(srid=4326, blank=True, null=True, verbose_name = _('ubication'))
    delimitation = geomodels.PolygonField(srid=4326, blank=True, null=True, verbose_name = _('delimitation'))
  
    # Estacion meteorológica
    station = models.ForeignKey(WeatherStation, models.SET_NULL, blank=True, null=True, verbose_name = _('weather station'))
    
    
    def _fill_default_cost_center(self):
        # Si no se completa, usa el centro de costo del campo o el centro de costo por defecto
        if not self.cost_center_id:
            countryside = self.countryside if self.countryside_id else None
            countryside_cc = countryside.cost_center if countryside else None
            producer = countryside.producer if countryside else None
            self.cost_center = countryside_cc or CostCenter.get_default(producer)

    def clean(self):
        super().clean()
        self._fill_default_cost_center()
        if not self.cost_center_id:
            raise ValidationError({'cost_center': _('This field is required.')})

    def save(self, *args, **kwargs):
        self._fill_default_cost_center()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name}"

    class Meta:
        verbose_name = _('lot')
        verbose_name_plural = _('lots')
        ordering = ['name']

    