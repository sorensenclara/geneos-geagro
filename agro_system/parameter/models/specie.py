from django.db import models
from django.utils.translation import gettext_lazy as _

class Specie(models.Model):

    """ Modelo para representar especies / variedades (Malbec, Trigo pan, etc.) """

    name = models.CharField(max_length=200, unique=True, verbose_name = _('name'))

    # GDD de cosecha — solo para variedades de vid (base 10°C desde brotación).
    # Null para cualquier otra especie.
    gdd_harvest_min = models.PositiveIntegerField(
        null=True, blank=True,
        verbose_name=_("GDD harvest min"),
        help_text=_("Base 10°C desde brotación. Ej: Malbec 1450. Vacío para no-vid."),
    )
    gdd_harvest_max = models.PositiveIntegerField(
        null=True, blank=True,
        verbose_name=_("GDD harvest max"),
        help_text=_("Base 10°C desde brotación. Ej: Malbec 1700. Vacío para no-vid."),
    )

    def __str__(self):
        return f"{self.name}"

    class Meta:
        verbose_name = _('specie')
        verbose_name_plural = _('species')