from django.db import models
from django.utils.translation import gettext_lazy as _
from .currency import Currency 


class exchangeRate(models.Model):

    """ Modelo para representar las tasas de cambio """

    currency_origin = models.ForeignKey(Currency, models.CASCADE,  verbose_name=_('currency origin'), related_name="currency_ori")
    currency_destination = models.ForeignKey(Currency, models.CASCADE,verbose_name=_('currency destination'),  related_name="currency_dest")
    date = models.DateField(verbose_name=_('date'))
    rate = models.FloatField( verbose_name=_('rate'))

    def __str__(self):
        return f"{self.currency_origin} → {self.currency_destination} | {self.rate}"

    class Meta:
        verbose_name = _('exchange rate')
        verbose_name_plural = _('exchange rates')