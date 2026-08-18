from django.db import models
from django.utils.translation import gettext_lazy as _


class Area(models.Model):
    """ Zona geográfica con clima y parámetros de cálculo de GDD. """

    CLIMATE_CHOICES = [
        ("Cfb_humid", _("Temperate humid (Cfb)")),
        ("BWk_arid",  _("Cold arid (BWk)")),
    ]

    name    = models.CharField(max_length=200, unique=True, verbose_name=_('name'))
    climate = models.CharField(
        max_length=20,
        choices=CLIMATE_CHOICES,
        null=True, blank=True,
        verbose_name=_("climate"),
    )

    # Techo de temperatura para GDD (método Winkler). Mendoza: 30.0. Tandil/no-vid: null.
    gdd_upper_cutoff = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        null=True, blank=True,
        verbose_name=_("GDD upper cutoff"),
        help_text=_("30.0 en Mendoza (Winkler con techo). Vacío en Tandil o zonas no-vid."),
    )

    def __str__(self):
        return f"{self.name}"

    class Meta:
        verbose_name = _('area')
        verbose_name_plural = _('areas')
