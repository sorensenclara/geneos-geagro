from django.db import models
from django.utils.translation import gettext_lazy as _

class Currency(models.Model):

    """ Modelo para representar las monedas """

    name = models.CharField(max_length=200, verbose_name=_('name'))
    symbol = models.CharField(max_length=10, blank=True, verbose_name=_('symbol'),
                              help_text=_('Símbolo corto para informes (ej: $ o USD)'))
    is_base = models.BooleanField(default=False, verbose_name=_('base currency'),
                                  help_text=_('Only one currency can be the base currency of the system'))
    def save(self, *args, **kwargs):
        if self.is_base:
            Currency.objects.exclude(pk=self.pk).update(is_base=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name}"

    class Meta:
        verbose_name = _('currency')
        verbose_name_plural = _('currencies')