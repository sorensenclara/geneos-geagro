from django.db import models
from producer.models.country_side import Countryside
from parameter.models.area import Area
from django.utils.translation import gettext_lazy as _
from producer.models.staff import Staff
from operation.models.activity import Activity
from parameter.models.campaign import Campaing
from producer.models.lot import Lot
from parameter.models.cultivation_state import CiltivationState
from parameter.models.port import Port

# Create your models here.

class Crop(models.Model):

    """ Modelo para representar cultivos """

    name = models.CharField(max_length=200, unique=True, verbose_name = _('name'))
    campaing = models.ForeignKey(Campaing, models.CASCADE,verbose_name = _('campaing'))
    countryside = models.ForeignKey(Countryside, models.CASCADE,verbose_name = _('countryside'))
    area = models.ForeignKey(Area, models.CASCADE,verbose_name = _('area'))
    lot = models.ForeignKey(Lot, models.CASCADE,verbose_name = _('lot'))
    activity = models.ForeignKey(Activity, on_delete=models.CASCADE, verbose_name = _('activity'))
    responsible = models.ForeignKey(Staff, models.CASCADE,verbose_name = _('responsible'))
    state = models.ForeignKey(CiltivationState, models.CASCADE, verbose_name = _('state'))
    hectares_productive = models.FloatField(default=0, verbose_name = _('hectares productive'))
    hectares_planted = models.FloatField(default=0, verbose_name = _('hectares planted'))
    hectares_unplanted = models.FloatField(default=0, verbose_name = _('hectares unplanted'))
    hectares_harvested = models.FloatField(default=0, verbose_name = _('hectares harvested'))
    hectares_not_harvested = models.FloatField(default=0, verbose_name = _('hectares not harvested'))
    impute_bills = models.BooleanField(default=True, verbose_name = _('inpute bills'))
    port = models.ForeignKey(Port, models.CASCADE, blank=True, null=True, verbose_name = _('port'))
    date_init = models.DateField(blank=True, null=True, verbose_name = _('date init'))
    freight_estimate = models.FloatField(blank=True, null=True,verbose_name = _('freight estimate') )
    estimate_saranda = models.FloatField(blank=True, null=True, verbose_name = _('estimate saranda'))
    estimate_secada = models.FloatField(blank=True, null=True, verbose_name = _('estimate secada'))
    producer = models.ForeignKey('user.UserProducer', on_delete=models.CASCADE, verbose_name = _('producer'))
    indicators = models.ManyToManyField('alert.Indicator', verbose_name = _('indicators'), null=True, blank=True)
    is_main = models.BooleanField(default=False, verbose_name = _('is main crop'), help_text=_('Indicates if this crop is the main crop of the staff. Only one crop can be the main crop for a staff.'))


    def __str__(self):
        return f"{self.campaing} - {self.countryside} / {self.lot} - {self.activity}"    

    class Meta:
        verbose_name = _('crop')
        verbose_name_plural = _('crops')