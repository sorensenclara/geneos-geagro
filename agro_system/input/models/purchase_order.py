from django.db import models
from django.utils.translation import gettext_lazy as _
from datetime import date
from .provider import Provider
from producer.models.staff import Staff
from producer.models.store import Store


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
    store = models.ForeignKey(Store, on_delete=models.CASCADE,verbose_name = _('store'))
    producer = models.ForeignKey('user.UserProducer', on_delete=models.RESTRICT, verbose_name= _('producer'))


    @property
    def code(self):
        return f"OC{self.number:04d}"

    def __str__(self):
        return self.code

    class Meta:
        verbose_name = _('purchase order')
        verbose_name_plural = _('purchase orders')
        ordering = ["-number"]
