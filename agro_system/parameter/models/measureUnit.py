from django.db import models
from django.utils.translation import gettext_lazy as _

class MaensureUnit(models.Model):

    """ Modelo para representar unidades de medida """

    name = models.CharField(max_length=200, unique=True, verbose_name = _('name'))
    is_reference = models.BooleanField(default=True, verbose_name=_('is reference unit'))
    mu_referenced = models.ForeignKey('MaensureUnit', models.CASCADE, blank=True, null=True, verbose_name=_('referenced unit'))
    multiplier = models.FloatField( verbose_name=_('multiplier'))
    

    def __str__(self):
        return f"{self.name}"

    class Meta:
        verbose_name = _('unit of measure')
        verbose_name_plural = _('units of measure')