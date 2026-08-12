from django.db import models
from django.utils.translation import gettext_lazy as _
from .work_order import WorkOrder
from input.models.input import Input
from producer.models.store import Store

class InputWorkOrder(models.Model):
    """ Modelo que representa los insumos de la orden de trabajo"""

    work_order = models.ForeignKey(WorkOrder, models.CASCADE, verbose_name= _('work order'))
    input = models.ForeignKey(Input, models.CASCADE, verbose_name= _('input'))
    dose = models.FloatField(verbose_name= _('planned dose'))
    dose_applied = models.FloatField(null=True, blank=True, verbose_name= _('dose applied'))
    value_estimated = models.FloatField(null=True, blank=True, verbose_name=_('estimated value (base currency)'))
    value_real = models.FloatField(null=True, blank=True, verbose_name=_('real value'))
    currency = models.ForeignKey('parameter.Currency', models.SET_NULL, null=True, blank=True, verbose_name=_('currency (real)'))
    exchange_rate = models.FloatField(null=True, blank=True, verbose_name=_('exchange rate'))
    value_real_base = models.FloatField(null=True, blank=True, verbose_name=_('real value (base currency)'))
    store = models.ForeignKey(Store, models.SET_NULL, null=True, blank=True, verbose_name=_('store'))
    details = models.TextField(null=True, blank=True, verbose_name= _('details'))

    def save(self, *args, **kwargs):
        if self.value_real is not None:
            if self.currency_id:
                from parameter.models.currency import Currency
                currency = Currency.objects.filter(pk=self.currency_id).first()
                if currency:
                    if currency.is_base:
                        self.exchange_rate = 1.0
                    elif not self.exchange_rate:
                        from parameter.models.exchange_rate import exchangeRate
                        producer = self.work_order.producer if self.work_order_id else None
                        fetched = exchangeRate.get_rate(currency, producer=producer)
                        if fetched:
                            self.exchange_rate = fetched
            rate = self.exchange_rate or 1.0
            self.value_real_base = round(self.value_real * rate, 2)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.work_order} - {self.input} - {self.dose}"

    class Meta:
        verbose_name =  _('input work order')
        verbose_name_plural =  _('inputs work orders')