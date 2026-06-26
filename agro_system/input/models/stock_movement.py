from django.db import models
from django.utils.translation import gettext_lazy as _
from datetime import date
from .input import Input
from producer.models.store import Store


class StockMovement(models.Model):

    OPERATIONS = [
        ('purchase',   _('Purchase')),    # Recepción de compra confirmada
        ('output',     _('Output')),       # Uso en orden de trabajo
        ('sale',       _('Sale')),         # Venta
        ('adjustment', _('Adjustment')),   # Ajuste manual de inventario
    ]

    date = models.DateField(default=date.today, verbose_name=_('date'))
    producer = models.ForeignKey(
        'user.UserProducer',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name=_('producer'),
    )
    input = models.ForeignKey(
        Input,
        on_delete=models.CASCADE,
        verbose_name=_('input'),
    )
    store = models.ForeignKey(
        Store,
        on_delete=models.CASCADE,
        verbose_name=_('store'),
    )
    # Positivo = entrada de stock, negativo = salida de stock
    quantity = models.FloatField(verbose_name=_('quantity'))
    stock_before = models.FloatField(verbose_name=_('stock before'))
    stock_after = models.FloatField(verbose_name=_('stock after'))
    operation = models.CharField(
        max_length=20,
        choices=OPERATIONS,
        verbose_name=_('operation'),
    )
    # Referencias al documento origen (solo uno es no-nulo para registros automáticos)
    purchase_reception = models.ForeignKey(
        'input.PurchaseReception',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name=_('purchase reception'),
    )
    work_order = models.ForeignKey(
        'operation.WorkOrder',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name=_('work order'),
    )
    notes = models.TextField(null=True, blank=True, verbose_name=_('notes'))

    def __str__(self):
        sign = '+' if self.quantity >= 0 else ''
        return f"{self.get_operation_display()} — {self.input} — {sign}{self.quantity} — {self.date}"

    class Meta:
        verbose_name = _('stock movement')
        verbose_name_plural = _('stock movements')
        ordering = ['-date', '-id']
