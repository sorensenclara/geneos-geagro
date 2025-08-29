from django.db import models

from django.utils.translation import gettext_lazy as _
from parameter.models.specie import Specie


class Activity(models.Model):

    """ Modelo para representar actividades """

    name = models.CharField(max_length=200, unique=True, verbose_name=_('name'))
    description = models.TextField(blank=True, null=True, verbose_name=_('description'))
    specie = models.ForeignKey(Specie, verbose_name=_('specie'), on_delete=models.CASCADE)
    is_agricultural = models.BooleanField(default=False, verbose_name=_('is agricultural'))
    is_livestock = models.BooleanField(default=False, verbose_name=_('is livestock'))


    def __str__(self):
        return f"{self.name}"

    class Meta:
        verbose_name = _('activity')
        verbose_name_plural = _('activities')