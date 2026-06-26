from django.db import models
from django.utils.translation import gettext_lazy as _
from parameter.models.silo_type import SiloType
from producer.models.country_side import Countryside
from producer.models.lot import Lot


class Silo(models.Model):

    """ Modelo para representar un silo de almacenamiento propio (metálico, bolsa, galpón, etc.) perteneciente a un campo """

    name = models.CharField(max_length=200, verbose_name=_('name'))
    type = models.ForeignKey(SiloType, on_delete=models.PROTECT, verbose_name=_('type'))
    capacity_tons = models.FloatField(verbose_name=_('capacity (tons)'))
    countryside = models.ForeignKey(Countryside, on_delete=models.CASCADE, verbose_name=_('countryside'))
    lot = models.ForeignKey(Lot, on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_('lot'),
                            help_text=_('Optional. Used for bag silos located in a specific lot.'))
    active = models.BooleanField(default=True, verbose_name=_('active'))
    producer = models.ForeignKey('user.UserProducer', on_delete=models.CASCADE, verbose_name=_('producer'))

    def __str__(self):
        return f"{self.name} ({self.countryside})"

    class Meta:
        verbose_name = _('silo')
        verbose_name_plural = _('silos')
        ordering = ['countryside', 'name']
