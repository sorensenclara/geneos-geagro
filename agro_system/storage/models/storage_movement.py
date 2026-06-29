from django.db import models
from django.utils.translation import gettext_lazy as _
from datetime import date
from parameter.models.port import Port
from .storage_certificate import StorageCertificate


class StorageMovement(models.Model):

    """ Modelo para representar un movimiento físico de granos sobre un certificado de depósito: puede ser un ingreso adicional, retiro parcial, salida a puerto/venta, o transferencia entre acopiadores """

    ENTRY = 'entry'
    SALE_EXIT = 'sale_exit'
    WITHDRAWAL = 'withdrawal'
    TRANSFER = 'transfer'
    TYPE_CHOICES = [
        (ENTRY, _('Entry')),
        (SALE_EXIT, _('Exit - Sale')),
        (WITHDRAWAL, _('Exit - Withdrawal')),
        (TRANSFER, _('Transfer to another storage')),
    ]

    certificate = models.ForeignKey(StorageCertificate, on_delete=models.CASCADE,
                                    related_name='movements', verbose_name=_('certificate'))
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, verbose_name=_('type'))
    date = models.DateField(default=date.today, verbose_name=_('date'))
    quantity_tons = models.FloatField(verbose_name=_('quantity (tons)'))
    remito_number = models.CharField(max_length=50, null=True, blank=True, verbose_name=_('remito number'))
    driver = models.ForeignKey('sale.Driver', on_delete=models.SET_NULL, null=True, blank=True,
                               verbose_name=_('driver'))
    destination = models.CharField(max_length=200, null=True, blank=True, verbose_name=_('destination'))
    port = models.ForeignKey(Port, on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_('port'))
    related_sale = models.ForeignKey('sale.SalesReceipt', on_delete=models.SET_NULL, null=True, blank=True,
                                     verbose_name=_('related sale'))
    notes = models.TextField(blank=True, verbose_name=_('notes'))
    producer = models.ForeignKey('user.UserProducer', on_delete=models.CASCADE, verbose_name=_('producer'))

    def save(self, *args, **kwargs):
        if not self.producer_id:
            self.producer = self.certificate.producer
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.get_type_display()} - {self.certificate} ({self.date})"

    class Meta:
        verbose_name = _('storage movement')
        verbose_name_plural = _('storage movements')
        ordering = ['-date', '-id']
