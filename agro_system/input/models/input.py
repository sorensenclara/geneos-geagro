from django.db import models
from django.utils.translation import gettext_lazy as _
from .type_input import TypeInput
from parameter.models.measure_unit import  MaensureUnit
from .category_input import CategoryInput
from parameter.models.currency import Currency

class Input(models.Model):

    """ Modelo para representar los insumos """

    name = models.CharField(max_length=200, unique=True, verbose_name = _('name'))
    type = models.ForeignKey(TypeInput, verbose_name = _('type of input'), on_delete=models.CASCADE)
    unit_measure = models.ForeignKey(MaensureUnit, models.CASCADE, verbose_name = _('unit of measure'))
    presentation = models.CharField(max_length=200, null=True, blank=True, verbose_name = _('presentation'))
    cost = models.FloatField(default=0, verbose_name = _('cost'))
    currency = models.ForeignKey(Currency, models.CASCADE, verbose_name=_('currency'))
    control_stock = models.BooleanField(default=True, verbose_name = _('control of stock'))
    stock = models.FloatField(default=0, verbose_name = _('stock'))
    min_stock = models.FloatField(default=0, verbose_name = _('reorder point')) # Punto de pedido
    pending = models.FloatField(default=0, verbose_name = _('pending'))
    control_lot = models.BooleanField(default=False, verbose_name = _('control of lot'))
    producer = models.ForeignKey('user.UserProducer', on_delete=models.RESTRICT, verbose_name= _('producer'), null=True, blank=True)

    def __str__(self):
        return f"{self.name}"

    class Meta:
        verbose_name = _('input')
        verbose_name_plural = _('inputs')
        ordering = ["name"]