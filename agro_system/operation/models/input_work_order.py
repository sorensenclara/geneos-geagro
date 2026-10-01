from django.db import models
from django.utils.translation import gettext_lazy as _
from .work_order import WorkOrder
from input.models.input import Input
from producer.models.store import Store

class InputWorkOrder(models.Model):
    """ Modelo que representa los insumos de la orden de trabajo"""

    work_order = models.ForeignKey(WorkOrder, models.CASCADE, verbose_name= _('work order'))
    input = models.ForeignKey(Input, models.CASCADE, verbose_name= _('input'))
    # Unidad de la labor: por defecto la del insumo (ver save), se puede cambiar
    unit_measure = models.ForeignKey('parameter.MaensureUnit', models.SET_NULL, null=True, blank=True, verbose_name=_('unit of measure'))
    dose = models.FloatField(verbose_name= _('technical dose (planned)'))
    dose_applied = models.FloatField(null=True, blank=True, verbose_name= _('real dose'))
    # Si queda vacía se calcula: dosis (real, o técnica si no hay real) x superficie de la orden
    total_quantity = models.FloatField(null=True, blank=True, verbose_name=_('total quantity'))
    value_estimated = models.FloatField(null=True, blank=True, verbose_name=_('estimated value (base currency)'))
    value_real = models.FloatField(null=True, blank=True, verbose_name=_('real value'))
    currency = models.ForeignKey('parameter.Currency', models.SET_NULL, null=True, blank=True, verbose_name=_('currency (real)'))
    exchange_rate = models.FloatField(null=True, blank=True, verbose_name=_('exchange rate'))
    value_real_base = models.FloatField(null=True, blank=True, verbose_name=_('real value (base currency)'))
    store = models.ForeignKey(Store, models.SET_NULL, null=True, blank=True, verbose_name=_('store'))
    details = models.TextField(null=True, blank=True, verbose_name= _('details'))

    def save(self, *args, **kwargs):
        if not self.unit_measure_id and self.input_id:
            self.unit_measure_id = self.input.unit_measure_id
        if self.total_quantity is None:
            self.total_quantity = self.calculated_total_quantity()
        if not self.store_id and self.work_order_id:
            countryside = self.work_order.crop.countryside
            self.store = countryside.store or Store.get_default(self.work_order.producer)
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

    def calculated_total_quantity(self):
        """Dosis (real, o técnica si no hay real) x superficie de la orden; None si falta algún dato."""
        dose = self.dose_applied if self.dose_applied is not None else self.dose
        surface = self.work_order.surface if self.work_order_id else None
        if dose is None or surface is None:
            return None
        return round(dose * surface, 2)

    @property
    def effective_unit(self):
        """Unidad de la labor; las líneas cargadas antes de existir el campo usan la del insumo."""
        return self.unit_measure or self.input.unit_measure

    def __str__(self):
        return f"{self.work_order} - {self.input} - {self.dose}"

    class Meta:
        verbose_name =  _('input work order')
        verbose_name_plural =  _('inputs work orders')