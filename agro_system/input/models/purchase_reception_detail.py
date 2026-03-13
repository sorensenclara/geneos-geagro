from django.db import models
from django.utils.translation import gettext_lazy as _
from producer.models.cost_center import CostCenter
from .purchase_reception import PurchaseReception
from .input import Input



class PurchaseReceptionDetail(models.Model):

    """ Modelo para representar los detalles de la recepcion de compra """


    purchase_reception = models.ForeignKey(PurchaseReception, models.CASCADE,  verbose_name = _('purchase order'))
    input = models.ForeignKey(Input, models.CASCADE, verbose_name = _('input'))
    amount = models.FloatField(default=0.0, verbose_name = _('amount'))
   

    def __str__(self):
        return f"{self.input} - {self.amount}"

    class Meta:
        verbose_name = _('purchase reception detail')
        verbose_name_plural = _('purchase reception details')

    