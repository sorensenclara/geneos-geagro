from django.db import models
from django.utils.translation import gettext_lazy as _
from .city  import City


class Port(models.Model):

    """ Modelo para representar puertos """

    name = models.CharField(max_length=200, unique=True, verbose_name = _('name'))
    city = models.ForeignKey(City, null=True, blank=True,  verbose_name = _('city'), on_delete=models.CASCADE) 

    def __str__(self):
        return f"{self.name}"

    class Meta:
        verbose_name = _('port')
        verbose_name_plural = _('ports')