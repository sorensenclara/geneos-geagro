from django.db import models
from django.utils.translation import gettext_lazy as _
from producer.models.costCenter import CostCenter
from .purchaseOrder import PurchaseOrder
from .input import Input



class PurchaseOrderDetail(models.Model):

    """ Modelo para representar el los detalles de la orden de compra """


    purchase_order = models.ForeignKey(PurchaseOrder, models.CASCADE,  verbose_name = _('purchase order'))
    input = models.ForeignKey(Input, models.CASCADE, verbose_name = _('input'))
    amount = models.FloatField(default=0.0, verbose_name =_('amount'))
    pending_amount = models.FloatField(null=True, blank=True,  verbose_name =_('pending amount'))
    price_unit = models.FloatField(null=True, blank=True,  verbose_name =_('price unit'))
    tax = models.FloatField(null=True, blank=True, verbose_name = _('taxes'))
    total = models.FloatField(null=True, blank=True,  verbose_name = _('price total'))
    costo_center = models.ForeignKey(CostCenter, models.CASCADE, null=True, blank=True, verbose_name = _('cost center'))

    def __str__(self):
        return f"{self.input} - {self.amount}"
    
    def save(self, *args, **kwargs):
        if not self.price_unit:
            self.price_unit = self.input.cost
        if self.price_unit and self.tax and self.amount:
            self.total = (self.price_unit+self.tax) * self.amount
        elif self.price_unit and self.amount:
            self.total = self.price_unit * self.amount
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = _('purchase order detail')
        verbose_name_plural = _('purchase order details')

    