from django.db import models
from django.utils.translation import gettext_lazy as _


class StorageServiceType(models.Model):

    """ Modelo para representar los tipos de servicio que ofrece un acopiador (secada, zaranda, fumigación, almacenaje, etc.) """

    name = models.CharField(max_length=100, unique=True, verbose_name=_('name'))

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _('storage service type')
        verbose_name_plural = _('storage service types')
        ordering = ['name']
