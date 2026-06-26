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
    
    code = models.CharField(max_length=20, unique=True, null=True, blank=True, verbose_name=_('code'))
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, verbose_name= _('purchase order'), null=True, blank=True)
    delivery_date = models.DateField(null=True, blank=True, verbose_name = _('delivery date'))
    reference = models.CharField(max_length=100, null=True, blank=True, verbose_name = _('reference'))
    state = models.CharField('Estado', max_length=7, choices=states, default='pending')
    store = models.ForeignKey(Store, on_delete=models.CASCADE, verbose_name = _('store'))
    producer = models.ForeignKey('user.UserProducer', on_delete=models.RESTRICT, verbose_name= _('producer'))

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        if is_new and not self.code:
            self.code = f"RC{self.pk:04d}"
            PurchaseReception.objects.filter(pk=self.pk).update(code=self.code)

    def __str__(self):
        return self.code if self.code else f"RC{self.pk:04d}"

    class Meta:
        verbose_name = _('purchase reception')
        verbose_name_plural = _('purchase receptions')
        ordering = ["-code"]