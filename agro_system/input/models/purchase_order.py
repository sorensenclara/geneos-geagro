from django.db import models
from django.utils.translation import gettext_lazy as _
from datetime import date
from .provider import Provider
from producer.models.staff import Staff
from producer.models.store import Store
from parameter.models.currency import Currency


class PurchaseOrder(models.Model):

    """ Modelo para representar la orden de compra """

    states = [
        ('pending', _('pending')),
        ('confirm', _('confirm')),
        ('cancel', _('cancel')),
    ]
    number = models.AutoField(primary_key=True, verbose_name = _('number'))
    date =  models.DateField(default=date.today(), verbose_name = _('date'))
    delivery_date = models.DateField(null=True, blank=True, verbose_name = _('delivery date'))
    reference = models.CharField(max_length=100, null=True, blank=True, verbose_name = _('reference'))
    applicant = models.ForeignKey(Staff, null=True, blank=True, on_delete=models.CASCADE, verbose_name = _('applicant'))
    provider = models.ForeignKey(Provider, on_delete=models.CASCADE, verbose_name = _('provider'))
    state = models.CharField('Estado', max_length=7, choices=states, default='pending')
    store = models.ForeignKey(Store, on_delete=models.CASCADE, blank=True, verbose_name=_('store'))
    currency = models.ForeignKey(Currency, on_delete=models.PROTECT, null=True, blank=True,
                                 verbose_name=_('currency'))
    exchange_rate = models.FloatField(null=True, blank=True, verbose_name=_('exchange rate'),
                                      help_text='How many units of the base currency equal 1 unit of the selected currency')
    producer = models.ForeignKey('user.UserProducer', on_delete=models.RESTRICT, verbose_name=_('producer'))


    def save(self, *args, **kwargs):
        if not self.store_id:
            self.store = Store.get_default(self.producer if self.producer_id else None)
        # Detectar si la tasa de cambio fue modificada antes de guardar
        rate_changed = False
        if self.pk:
            try:
                old = PurchaseOrder.objects.get(pk=self.pk)
                rate_changed = old.exchange_rate != self.exchange_rate
            except PurchaseOrder.DoesNotExist:
                pass

        super().save(*args, **kwargs)

        # Si la tasa cambió y la orden sigue pendiente, recalcular total_base en todos los detalles
        if rate_changed and self.state == 'pending':
            for detail in self.purchaseorderdetail_set.all():
                detail.save()

    @property
    def code(self):
        return f"OC{self.number:04d}"

    def __str__(self):
        return self.code

    class Meta:
        verbose_name = _('purchase order')
        verbose_name_plural = _('purchase orders')
        ordering = ["-number"]
