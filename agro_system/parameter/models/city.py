from django.db import models
from django.utils.translation import gettext_lazy as _
from .province import Province


class City(models.Model):

    """ Modelo para representar ciudades """

    name = models.CharField(max_length=200, verbose_name = _('name'))
    province = models.ForeignKey(Province, on_delete=models.CASCADE, verbose_name=_('province'))

    def __str__(self):
        return f"{self.name}"

    class Meta:
        verbose_name = _('city')
        verbose_name_plural = _('cities')
    
        unique_together = ('name', 'province')