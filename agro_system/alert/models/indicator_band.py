from django.db import models
from django.utils.translation import gettext_lazy as _


class IndicatorBand(models.Model):
    """
    Defines alert severity based on BBCH range (numeric) and the value of the
    graduated variable for a given Indicator.

    Example for frost (Mendoza):
      (bbch_from=1,  bbch_to=5,  threshold=-3.5, level='alert')
      (bbch_from=1,  bbch_to=5,  threshold=-5.0, level='critical')
      (bbch_from=11, bbch_to=27, threshold=-1.0, level='alert')

    The evaluator finds the band matching the current BBCH, orders by 'order'
    and applies the first exceeded threshold.
    """

    LEVEL_CHOICES = [
        ("warning",  _("Warning")),
        ("alert",    _("Alert")),
        ("critical", _("Critical")),
    ]

    DIRECTION_CHOICES = [
        ("gte", _("≥ threshold (higher is worse)")),
        ("lte", _("≤ threshold (lower is worse)")),
    ]

    indicator  = models.ForeignKey(
        "alert.Indicator",
        on_delete=models.CASCADE,
        related_name="bands",
        verbose_name=_("indicator"),
    )
    bbch_from  = models.PositiveSmallIntegerField(verbose_name=_("BBCH from (numeric)"))
    bbch_to    = models.PositiveSmallIntegerField(verbose_name=_("BBCH to (numeric)"))
    threshold  = models.DecimalField(
        max_digits=6, decimal_places=2,
        null=True, blank=True,
        verbose_name=_("threshold"),
        help_text=_("Leave blank to fire on BBCH match alone (no graduated variable)."),
    )
    direction  = models.CharField(
        max_length=3,
        choices=DIRECTION_CHOICES,
        null=True, blank=True,
        verbose_name=_("direction"),
    )
    level      = models.CharField(max_length=8, choices=LEVEL_CHOICES, verbose_name=_("level"))
    order      = models.PositiveSmallIntegerField(default=1, verbose_name=_("order"))

    class Meta:
        ordering = ["bbch_from", "order"]
        verbose_name        = _("indicator band")
        verbose_name_plural = _("indicator bands")

    def crosses(self, value=None) -> bool:
        """True if value crosses this band's threshold, or always True when threshold is NULL."""
        if self.threshold is None:
            return True
        if value is None:
            return False
        if self.direction == "gte":
            return value >= float(self.threshold)
        return value <= float(self.threshold)

    def __str__(self):
        if self.threshold is None:
            condition = "any"
        else:
            op = "≥" if self.direction == "gte" else "≤"
            condition = f"{op} {self.threshold}"
        return f"BBCH {self.bbch_from}–{self.bbch_to} | {condition} → {self.level}"
