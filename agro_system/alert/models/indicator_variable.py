from django.db import models
from django.utils.translation import gettext_lazy as _
from parameter.models.var_crop_technique import VarCropTechnique
from .indicator import Indicator


class IndicatorVariable(models.Model):
    """
    A variable condition attached to an Indicator.

    role='filter'   — must be within [min_value, max_value] for the indicator to fire.
                      ALL filter variables must pass (AND logic).
                      Example: wind between 0 and 8 km/h for spray window.

    role='graduated' — its value is compared against NivelPorBanda to determine
                       the severity level (warning / alert / critical).
                       Example: t_min for frost.
    """

    ROLE_FILTER   = "filter"
    ROLE_GRADUATED = "graduated"
    ROLE_CHOICES = [
        (ROLE_FILTER,    _("Filter — must be in range for indicator to fire")),
        (ROLE_GRADUATED, _("Graduated — determines severity via BBCH bands")),
    ]

    indicator = models.ForeignKey(
        Indicator,
        on_delete=models.CASCADE,
        related_name="variables",
        verbose_name=_("indicator"),
    )
    variable = models.ForeignKey(
        VarCropTechnique,
        on_delete=models.CASCADE,
        verbose_name=_("variable"),
    )
    LEVEL_ANY      = ""
    LEVEL_WARNING  = "warning"
    LEVEL_ALERT    = "alert"
    LEVEL_CRITICAL = "critical"
    LEVEL_CHOICES  = [
        (LEVEL_ANY,      _("Any level (no restriction)")),
        (LEVEL_WARNING,  _("Warning")),
        (LEVEL_ALERT,    _("Alert")),
        (LEVEL_CRITICAL, _("Critical")),
    ]

    min_value   = models.FloatField(null=True, blank=True, verbose_name=_("min value"))
    max_value   = models.FloatField(null=True, blank=True, verbose_name=_("max value"))
    alert_level = models.CharField(
        max_length=10,
        choices=LEVEL_CHOICES,
        default="",
        blank=True,
        verbose_name=_("alert level"),
        help_text=_("Level this threshold triggers. Empty = applies to all levels."),
    )
    role        = models.CharField(
        max_length=10,
        choices=ROLE_CHOICES,
        default="filter",
        verbose_name=_("role"),
    )
    order = models.PositiveIntegerField(default=1, verbose_name=_("order"))

    class Meta:
        ordering = ["order"]
        verbose_name = _("indicator variable")
        verbose_name_plural = _("indicator variables")

    def __str__(self):
        return f"{self.indicator} — {self.variable} [{self.min_value}, {self.max_value}] ({self.role})"
