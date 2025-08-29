from django.db import models
from django.utils.translation import gettext_lazy as _
from .country import Country


class Province(models.Model):

    """Modelo para representar provincias"""

    name = models.CharField(max_length=200, unique=True, verbose_name = _('name'))
    country = models.ForeignKey(Country, on_delete=models.CASCADE, verbose_name=_('country'))

    def __str__(self):
        return f"{self.name}"

    class Meta:
        verbose_name = _('province')
        verbose_name_plural = _('provinces')