from django.db import models
from django.utils.translation import gettext_lazy as _

class CostCenter(models.Model):

    """ Modelo para representar el centro de costo"""

    name = models.CharField(max_length=200, unique=True, verbose_name = _('name'))

    def __str__(self):
        return f"{self.name}"

    class Meta:
        verbose_name = _('center of cost')
        verbose_name_plural = _('centes of cost')