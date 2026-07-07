from django.db import models
from django.utils.translation import gettext_lazy as _
from .type_input import TypeInput
from parameter.models.measure_unit import MaensureUnit
from parameter.models.currency import Currency
from parameter.models.exchange_rate import exchangeRate


COST_UPDATE_CHOICES = [
    ('manual', _('Manual')),
    ('last_purchase', _('Last purchase price (in base currency)')),
    ('campaign_avg', _('Weighted average of current campaign (in base currency)')),
]


class Input(models.Model):

    """ Modelo para representar los insumos """

    name = models.CharField(max_length=200, unique=True, verbose_name=_('name'))
    type = models.ForeignKey(TypeInput, verbose_name=_('type of input'), on_delete=models.CASCADE)
    unit_measure = models.ForeignKey(MaensureUnit, models.CASCADE, verbose_name=_('unit of measure'))
    presentation = models.CharField(max_length=200, null=True, blank=True, verbose_name=_('presentation'))
    cost = models.FloatField(default=0, verbose_name=_('cost'))
    currency = models.ForeignKey(Currency, models.CASCADE, verbose_name=_('currency'))
    cost_base = models.FloatField(null=True, blank=True, verbose_name=_('cost in base currency'))
    cost_update_mode = models.CharField(
        max_length=20,
        choices=COST_UPDATE_CHOICES,
        default='manual',
        verbose_name=_('cost update mode'),
        help_text=_('Determines how the base cost is updated when a purchase is confirmed'),
    )
    control_stock = models.BooleanField(default=True, verbose_name=_('control of stock'))
    stock = models.FloatField(default=0, verbose_name=_('stock'))
    min_stock = models.FloatField(default=0, verbose_name=_('reorder point'), help_text=_('Minimum stock level to trigger a reorder'))
    pending = models.FloatField(default=0, verbose_name=_('pending'))
    control_lot = models.BooleanField(default=False, verbose_name=_('control of lot'))
    producer = models.ForeignKey('user.UserProducer', on_delete=models.RESTRICT, verbose_name=_('producer'), null=True, blank=True)

    def save(self, *args, **kwargs):
        # Solo auto-calcula cost_base en modo manual; los otros modos lo gestionan al confirmar compras
        if self.cost_update_mode == 'manual' and self.cost and self.currency_id:
            currency = Currency.objects.filter(pk=self.currency_id).first()
            if currency:
                if currency.is_base:
                    self.cost_base = self.cost
                else:
                    rate = exchangeRate.get_rate(currency)
                    self.cost_base = round(self.cost * rate, 2) if rate else None
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name}"

    class Meta:
        verbose_name = _('input')
        verbose_name_plural = _('inputs')
        ordering = ["name"]
