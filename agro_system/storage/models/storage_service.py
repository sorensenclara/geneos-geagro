from django.db import models
from django.utils.translation import gettext_lazy as _
from datetime import date
from parameter.models.storage_service_type import StorageServiceType
from parameter.models.currency import Currency
from .storage_certificate import StorageCertificate


class StorageService(models.Model):

    """ Modelo para representar un servicio aplicado por el acopiador sobre el cereal depositado (secada, zaranda, fumigación, etc.) con su costo y resultado de calidad """

    certificate = models.ForeignKey(StorageCertificate, on_delete=models.CASCADE,
                                    related_name='services', verbose_name=_('certificate'))
    type = models.ForeignKey(StorageServiceType, on_delete=models.PROTECT, verbose_name=_('service type'))
    date = models.DateField(default=date.today, verbose_name=_('date'))
    quantity_affected = models.FloatField(verbose_name=_('quantity affected (tons)'))
    shrinkage_tons = models.FloatField(default=0, verbose_name=_('shrinkage (tons)'))
    humidity_result = models.FloatField(null=True, blank=True, verbose_name=_('resulting humidity (%)'))
    cost = models.FloatField(verbose_name=_('cost'))
    currency = models.ForeignKey(Currency, on_delete=models.PROTECT, verbose_name=_('currency'))
    notes = models.TextField(blank=True, verbose_name=_('notes'))

    def __str__(self):
        return f"{self.type} - {self.certificate} ({self.date})"

    class Meta:
        verbose_name = _('storage service')
        verbose_name_plural = _('storage services')
        ordering = ['-date']
