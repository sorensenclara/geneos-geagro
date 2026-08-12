from django.db import models
from django.utils.translation import gettext_lazy as _
from .currency import Currency


class exchangeRate(models.Model):

    """ Modelo para representar las tasas de cambio respecto a la moneda base """

    currency_origin = models.ForeignKey(Currency, models.CASCADE, verbose_name=_('currency origin'), related_name="currency_ori")
    currency_destination = models.ForeignKey(Currency, models.CASCADE, verbose_name=_('currency destination'), related_name="currency_dest")
    date = models.DateField(verbose_name=_('date'))
    rate = models.FloatField(verbose_name=_('rate to base currency'),
                             help_text='How many units of the base currency equal 1 unit of the origin currency')
    producer = models.ForeignKey(
        'user.UserProducer',
        on_delete=models.CASCADE,
        null=True, blank=True,
        verbose_name=_('producer'),
        help_text=_('Leave empty for global rates (used as fallback for all producers)'),
    )

    def __str__(self):
        return f"{self.currency_origin} → {self.currency_destination} | {self.rate}"

    @classmethod
    def get_rate(cls, from_currency, producer=None):
        """
        Devuelve la tasa más reciente de from_currency a la moneda base.
        Si se pasa producer, busca primero su tasa específica; si no hay, usa la global (producer=null).
        Si from_currency ya es la base, devuelve 1.0.
        Si no hay tasa registrada, devuelve None.
        """
        base = Currency.objects.filter(is_base=True).first()
        if not base:
            return None
        if from_currency.pk == base.pk:
            return 1.0
        qs = cls.objects.filter(
            currency_origin=from_currency,
            currency_destination=base,
        )
        if producer:
            record = qs.filter(producer=producer).order_by('-date').first()
            if record:
                return record.rate
            # Fallback a tasa global
        record = qs.filter(producer__isnull=True).order_by('-date').first()
        return record.rate if record else None

    @classmethod
    def convert(cls, amount, from_currency):
        """
        Convierte amount desde from_currency a la moneda base.
        Devuelve None si no hay tasa disponible.
        """
        rate = cls.get_rate(from_currency)
        if rate is None:
            return None
        return amount * rate

    class Meta:
        verbose_name = _('exchange rate')
        verbose_name_plural = _('exchange rates')
        ordering = ['-date']