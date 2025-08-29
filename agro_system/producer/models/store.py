from django.db import models
from django.utils.translation import gettext_lazy as _
from parameter.models.city import City


class Store(models.Model):

    """ Modelo para representar los almacenes """

    name = models.CharField(max_length=200, unique=True, verbose_name = _('name'))
    address = models.CharField(max_length=50, verbose_name = _('address'))
    city = models.ForeignKey(City, models.CASCADE, verbose_name = _('city'))

    def __str__(self):
        return f"{self.name}"

    class Meta:
        verbose_name = _('Store')
        verbose_name_plural = _('Stores')