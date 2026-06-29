from django.db import models
from django.utils.translation import gettext_lazy as _
from datetime import date
from .silo import Silo
from .silo_stock import SiloStock


class SiloMovement(models.Model):

    """ Modelo para representar un movimiento de granos en un silo propio: entrada de cosecha, salida a venta o a acopiador, o transferencia entre silos """

    ENTRY = 'entry'
    EXIT = 'exit'
    TRANSFER = 'transfer'
    TYPE_CHOICES = [
        (ENTRY, _('Entry')),
        (EXIT, _('Exit')),
        (TRANSFER, _('Transfer to another silo')),
    ]

    silo = models.ForeignKey(Silo, on_delete=models.CASCADE, related_name='movements', verbose_name=_('silo'))
    silo_stock = models.ForeignKey(SiloStock, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='movements', verbose_name=_('silo stock'))
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, verbose_name=_('type'))
    date = models.DateField(default=date.today, verbose_name=_('date'))
    quantity_tons = models.FloatField(verbose_name=_('quantity (tons)'))
    destination_silo = models.ForeignKey(Silo, on_delete=models.SET_NULL, null=True, blank=True,
                                         related_name='incoming_transfers', verbose_name=_('destination silo'),
                                         help_text=_('Only for transfer movements.'))
    related_sale = models.ForeignKey('sale.SalesReceipt', on_delete=models.SET_NULL, null=True, blank=True,
                                     verbose_name=_('related sale'))
    remito_number = models.CharField(max_length=50, null=True, blank=True, verbose_name=_('remito number'))
    driver = models.ForeignKey('sale.Driver', on_delete=models.SET_NULL, null=True, blank=True,
                               verbose_name=_('driver'))
    notes = models.TextField(blank=True, verbose_name=_('notes'))
    producer = models.ForeignKey('user.UserProducer', on_delete=models.CASCADE, verbose_name=_('producer'))

    def save(self, *args, **kwargs):
        if not self.producer_id:
            self.producer = self.silo.producer
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.get_type_display()} - {self.silo} ({self.date})"

    class Meta:
        verbose_name = _('silo movement')
        verbose_name_plural = _('silo movements')
        ordering = ['-date', '-id']
