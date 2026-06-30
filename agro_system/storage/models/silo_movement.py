from django.db import models
from django.db.models import Sum, Q
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
    crop = models.ForeignKey('operation.Crop', on_delete=models.SET_NULL, null=True, blank=True,
                             verbose_name=_('crop'))
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
    silo_stock = models.ForeignKey(SiloStock, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='movements', verbose_name=_('silo stock'))
    
    def save(self, *args, **kwargs):
        if not self.producer_id:
            self.producer = self.silo.producer
        super().save(*args, **kwargs)
        self._sync_stock()

    def _sync_stock(self):
        if not self.crop_id:
            return
        # Sync stock del silo origen
        stock, created = self._sync_silo_stock(self.silo, self.crop)
        if self.silo_stock_id != stock.pk:
            SiloMovement.objects.filter(pk=self.pk).update(silo_stock=stock)
        self._synced_stock_pk = stock.pk
        self._synced_stock_created = created
        # Para transferencias, también actualizar/crear el stock del silo destino
        if self.type == self.TRANSFER and self.destination_silo_id:
            self._sync_silo_stock(self.destination_silo, self.crop)

    def _sync_silo_stock(self, silo, crop):
        stock, created = SiloStock.objects.get_or_create(
            silo=silo,
            crop=crop,
            defaults={
                'specie': crop.activity.specie,
                'campaing': crop.campaing,
                'quantity_tons': 0,
                'active': True,
            }
        )
        totals = SiloMovement.objects.filter(silo=silo, crop=crop).aggregate(
            entradas=Sum('quantity_tons', filter=Q(type=self.ENTRY)),
            salidas=Sum('quantity_tons', filter=Q(type__in=[self.EXIT, self.TRANSFER])),
        )
        # Las transferencias recibidas suman como entrada al silo destino
        incoming = SiloMovement.objects.filter(
            destination_silo=silo, crop=crop, type=self.TRANSFER
        ).aggregate(total=Sum('quantity_tons'))['total'] or 0
        quantity = max(
            (totals['entradas'] or 0) - (totals['salidas'] or 0) + incoming,
            0
        )
        SiloStock.objects.filter(pk=stock.pk).update(
            quantity_tons=quantity,
            active=quantity > 0,
        )
        return stock, created

    def __str__(self):
        crop_str = f" [{self.crop}]" if self.crop else ""
        return f"{self.get_type_display()}{crop_str} - {self.silo} ({self.date})"

    class Meta:
        verbose_name = _('silo movement')
        verbose_name_plural = _('silo movements')
        ordering = ['-date', '-id']
