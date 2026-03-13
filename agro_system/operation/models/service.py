from django.db import models
from django.utils.translation import gettext_lazy as _
from .service_type import ServiceType


class Service(models.Model):

    """ Modelo para representar los servicios """

    name = models.CharField(max_length=200, unique=True, verbose_name = _('name'))
    type = models.ForeignKey(ServiceType, verbose_name = _('type of service'), on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.name}"

    class Meta:
        verbose_name = _('service')
        verbose_name_plural = _('services')