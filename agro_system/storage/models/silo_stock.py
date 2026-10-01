from django.db import models
from django.utils.translation import gettext_lazy as _
from datetime import date
from parameter.models.specie import Specie
from parameter.models.campaign import Campaing
from .silo import Silo


class SiloStock(models.Model):

    """ Modelo para representar el stock de granos almacenado en un silo propio, discriminado por especie y campaña. Registra la calidad al momento del ingreso. """

    silo = models.ForeignKey(Silo, on_delete=models.CASCADE, related_name='stocks', verbose_name=_('silo'))
    specie = models.ForeignKey(Specie, on_delete=models.PROTECT, verbose_name=_('specie'))
    campaing = models.ForeignKey(Campaing, on_delete=models.PROTECT, verbose_name=_('campaing'))
    crop = models.ForeignKey('operation.Crop', on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_('crop'))
    quantity_tons = models.FloatField(default=0, verbose_name=_('quantity (tons)'))
    active = models.BooleanField(default=True, verbose_name=_('vigente'))
    humidity_pct = models.FloatField(null=True, blank=True, verbose_name=_('humidity (%)'))
    impurities_pct = models.FloatField(null=True, blank=True, verbose_name=_('impurities (%)'))
    protein_pct = models.FloatField(null=True, blank=True, verbose_name=_('protein (%)'))
    test_weight = models.FloatField(null=True, blank=True, verbose_name=_('test weight (kg/hl)'))
    date_entry = models.DateField(default=date.today, verbose_name=_('date of last movement'))

    def save(self, *args, **kwargs):
        if self.crop_id:
            self.specie = self.crop.variety.specie
            self.campaing = self.crop.campaing
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.silo} - {self.specie} ({self.campaing})"

    class Meta:
        verbose_name = _('silo stock')
        verbose_name_plural = _('silo stocks')
        unique_together = [('silo', 'specie', 'campaing')]
        ordering = ['-date_entry']
