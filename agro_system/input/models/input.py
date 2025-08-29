from django.db import models
from django.utils.translation import gettext_lazy as _
from .typeInput import TypeInput
from parameter.models.measureUnit import  MaensureUnit
from .categoryInput import CategoryInput
from parameter.models.currency import Currency

class Input(models.Model):

    """ Modelo para representar los insumos """

    name = models.CharField(max_length=200, unique=True, verbose_name = _('name'))
    type = models.ForeignKey(TypeInput, verbose_name = _('type of input'), on_delete=models.CASCADE)
    unit_measure = models.ForeignKey(MaensureUnit, models.CASCADE, verbose_name = _('unit of measure'))
    category = models.ForeignKey(CategoryInput, models.CASCADE, verbose_name = _('category'))
    presentation = models.CharField(max_length=200, null=True, blank=True, verbose_name = _('presentation'))
    cost = models.FloatField(default=0, verbose_name = _('cost'))
    currency = models.ForeignKey(Currency, models.CASCADE, verbose_name=_('currency'))
    control_stock = models.BooleanField(default=True, verbose_name = _('control of stock'))
    stock = models.FloatField(default=0, verbose_name = _('stock'))
    pending = models.FloatField(default=0, verbose_name = _('pending'))
    control_lot = models.BooleanField(default=False, verbose_name = _('control of lot'))

    def __str__(self):
        return f"{self.name}"

    class Meta:
        verbose_name = _('input')
        verbose_name_plural = _('inputs')