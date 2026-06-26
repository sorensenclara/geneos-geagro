from django.db import models
from django.utils.translation import gettext_lazy as _


class SiloType(models.Model):

    """ Modelo para representar los tipos de silo (metálico, bolsa plástica, galpón, etc.) """

    name = models.CharField(max_length=100, unique=True, verbose_name=_('name'))

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _('silo type')
        verbose_name_plural = _('silo types')
        ordering = ['name']
