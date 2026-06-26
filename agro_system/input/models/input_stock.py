from django.db import models
from django.utils.translation import gettext_lazy as _
from .input import Input
from producer.models.store import Store


class InputStock(models.Model):

    input = models.ForeignKey(
        Input,
        on_delete=models.CASCADE,
        verbose_name=_('input'),
        related_name='stock_by_store',
    )
    store = models.ForeignKey(
        Store,
        on_delete=models.CASCADE,
        verbose_name=_('store'),
        related_name='input_stocks',
    )
    quantity = models.FloatField(default=0, verbose_name=_('quantity'))

    class Meta:
        unique_together = [('input', 'store')]
        verbose_name = _('stock per store')
        verbose_name_plural = _('stock per store')
        ordering = ['store', 'input']

    def __str__(self):
        return f"{self.input} — {self.store}: {self.quantity}"
