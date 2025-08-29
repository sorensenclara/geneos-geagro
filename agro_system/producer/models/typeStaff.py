from django.db import models
from django.utils.translation import gettext_lazy as _



class TypeStaff(models.Model):

    """ Modelo para representar los tipos de personal"""

    name = models.CharField(max_length=200, unique=True, verbose_name = _('name'))

    def __str__(self):
        return f"{self.name}"

    class Meta:
        verbose_name = _('type of staff')
        verbose_name_plural = _('types of staff')