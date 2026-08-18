from django.db import models
from django.utils.translation import gettext_lazy as _


class AlertProfileIndicator(models.Model):
    """
    Activates an Indicator for a zone (AlertProfile) with a given status.
    Replaces the active_alerts JSONField on AlertProfile.

    Each row means: "zone X has indicator Y with status Z".
    Thresholds for that indicator live in NivelPorBanda (bands) on the Indicator itself.
    """

    STATUS_CHOICES = [
        ("on",          _("On — evaluates and notifies")),
        ("vigilance",   _("Vigilance — evaluates, records only")),
        ("off",         _("Off — not evaluated")),
    ]

    profile   = models.ForeignKey(
        "alert.AlertProfile",
        on_delete=models.CASCADE,
        related_name="profile_indicators",
        verbose_name=_("alert profile"),
    )
    indicator = models.ForeignKey(
        "alert.Indicator",
        on_delete=models.CASCADE,
        related_name="profile_links",
        verbose_name=_("indicator"),
    )
    status = models.CharField(
        max_length=12,
        choices=STATUS_CHOICES,
        default="on",
        verbose_name=_("status"),
    )

    class Meta:
        unique_together = ("profile", "indicator")
        ordering = ["indicator__name"]
        verbose_name        = _("profile indicator")
        verbose_name_plural = _("profile indicators")

    def __str__(self):
        return f"{self.profile.area} — {self.indicator} [{self.status}]"
