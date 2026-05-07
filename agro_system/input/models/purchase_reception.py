from django.db import models
from django.utils.translation import gettext_lazy as _
from producer.models.store import Store
from .purchase_order import PurchaseOrder

class PurchaseReception(models.Model):

    """ Modelo para representar la recepcion de la compra """

    states = [
        ('pending', _('pending')),
        ('confirm', _('confirm')),
        ('cancel', _('cancel')),
    ]
    
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, verbose_name= _('purchase order'), null=True, blank=True)
    delivery_date = models.DateField(null=True, blank=True, verbose_name = _('delivery date'))
    reference = models.CharField(max_length=100, null=True, blank=True, verbose_name = _('reference'))
    state = models.CharField('Estado', max_length=7, choices=states, default='pending')
    store = models.ForeignKey(Store, on_delete=models.CASCADE,verbose_name = _('store'))
    producer = models.ForeignKey('user.UserProducer', on_delete=models.RESTRICT, verbose_name= _('producer'))
   
    
    def __str__(self):
        return f"{self.delivery_date} - {self.reference}"

    class Meta:
        verbose_name = _('purchase reception')
        verbose_name_plural = _('purchase receptions')
        ordering = ["delivery_date"]