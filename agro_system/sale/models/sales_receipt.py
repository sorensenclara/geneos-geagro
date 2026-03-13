from django.db import models
from django.utils.translation import gettext_lazy as _
from .type_sales_receipt import TypeSalesReceipt
from agro_system.validacions import validation_cuit 
from datetime import date
from parameter.models.currency import Currency
from parameter.models.campaign import Campaing
from parameter.models.specie import Specie
from producer.models.cost_center import CostCenter
from input.models.provider import Provider
from sale.models.driver import Driver

class SalesReceipt(models.Model):

    """ Modelo para representar los comprobantes de venta"""
    
    date =  models.DateField(default=date.today(), verbose_name = _('date'))
    type = models.ForeignKey(TypeSalesReceipt, on_delete=models.CASCADE, verbose_name = _('type of sales receipt'))
    number = models.CharField(max_length=200, unique=True, verbose_name = _('number'))
    currency = models.ForeignKey(Currency, on_delete=models.CASCADE, verbose_name = _('currency') )
    name_custom = models.CharField(max_length=200, verbose_name = _('custom'))
    cuit_custom= models.CharField(max_length=11, validators=[validation_cuit], verbose_name = _('cuil of custom'))
    campaing = models.ForeignKey(Campaing, on_delete=models.CASCADE, verbose_name="campaing")
    cost_center = models.ForeignKey(CostCenter, on_delete=models.CASCADE, null=True, blank=True, verbose_name = _('cost center'))
    especie = models.ForeignKey(Specie, on_delete=models.CASCADE, null=True, blank=True, verbose_name = _('especie'))
    amount = models.FloatField(default=0, verbose_name = _('amount'))
    subtotal = models.FloatField(default=0, verbose_name = _('subtotal'))
    taxes = models.FloatField(default=0, verbose_name = _('taxes'))
    provider = models.ForeignKey(Provider, on_delete=models.CASCADE, null=True, blank=True, verbose_name = _('provider'))
    driver = models.ForeignKey(Driver, on_delete=models.CASCADE, null=True, blank=True, verbose_name = _('driver'))
    producer = models.ForeignKey('user.UserProducer', on_delete=models.RESTRICT, verbose_name= _('producer'))

    def __str__(self):
        return f"{self.number}"

    class Meta:
        verbose_name = _('sales receipt')
        verbose_name_plural = _('sales receipts')
        ordering = ["date"]
    
    @property
    def total(self):
        return self.subtotal + self.taxes
    