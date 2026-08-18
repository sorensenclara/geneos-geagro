from django.db import models
from django.utils.translation import gettext_lazy as _


class AlertProfile(models.Model):
    """
    Alert engine configuration for a geographic zone (Area).
    One profile per area; if the area has no profile the engine skips it.

    Which indicators are active and with what status lives in AlertProfileIndicator.
    Threshold bands live in IndicatorBand on each Indicator.
    """

    area = models.OneToOneField(
        "parameter.Area",
        on_delete=models.CASCADE,
        related_name="alert_profile",
        verbose_name=_("area"),
    )

    priority_sources = models.JSONField(
        default=list,
        blank=True,
        verbose_name=_("priority sources"),
        help_text=_(
            'Priority order of meteorological data sources for this zone. '
            'Example: ["open_meteo_eto", "soil_moisture_station", "station"].'
        ),
    )

    def __str__(self):
        return f"AlertProfile — {self.area}"

    class Meta:
        verbose_name        = _("alert profile")
        verbose_name_plural = _("alert profiles")
