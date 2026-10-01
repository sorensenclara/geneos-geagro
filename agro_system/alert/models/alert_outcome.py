from django.db import models
from django.utils.translation import gettext_lazy as _


class AlertOutcome(models.Model):
    """ Modelo para registrar el resultado de una alerta  """

    SEVERITY_NONE     = "none"
    SEVERITY_MINOR    = "minor"
    SEVERITY_MODERATE = "moderate"
    SEVERITY_SEVERE   = "severe"
    SEVERITY_TOTAL    = "total"
    SEVERITY_CHOICES = [
        (SEVERITY_NONE,     _("No damage")),
        (SEVERITY_MINOR,    _("Minor")),
        (SEVERITY_MODERATE, _("Moderate")),
        (SEVERITY_SEVERE,   _("Severe")),
        (SEVERITY_TOTAL,    _("Total loss")),
    ]

    EFFECTIVENESS_YES     = "yes"
    EFFECTIVENESS_PARTIAL = "partial"
    EFFECTIVENESS_NO      = "no"
    EFFECTIVENESS_NA      = "na"
    EFFECTIVENESS_CHOICES = [
        (EFFECTIVENESS_YES,     _("Effective")),
        (EFFECTIVENESS_PARTIAL, _("Partially effective")),
        (EFFECTIVENESS_NO,      _("Not effective")),
        (EFFECTIVENESS_NA,      _("Not applicable / no intervention")),
    ]

    alert = models.OneToOneField(
        "alert.Alert",
        on_delete=models.CASCADE,
        related_name="outcome",
        verbose_name=_("alert"),
    )

    damage_occurred = models.BooleanField(
        default=False,
        verbose_name=_("damage occurred"),
    )
    damage_severity = models.CharField(
        max_length=10,
        choices=SEVERITY_CHOICES,
        default=SEVERITY_NONE,
        verbose_name=_("damage severity"),
    )
    area_affected_pct = models.DecimalField(
        max_digits=5, decimal_places=1,
        null=True, blank=True,
        verbose_name=_("area affected (%)"),
    )
    estimated_loss_kg_ha = models.DecimalField(
        max_digits=8, decimal_places=1,
        null=True, blank=True,
        verbose_name=_("estimated loss (kg/ha)"),
    )
    estimated_loss_ars = models.DecimalField(
        max_digits=12, decimal_places=2,
        null=True, blank=True,
        verbose_name=_("estimated economic loss ($)"),
    )
    intervention_effective = models.CharField(
        max_length=10,
        choices=EFFECTIVENESS_CHOICES,
        default=EFFECTIVENESS_NA,
        verbose_name=_("intervention effectiveness"),
    )
    notes = models.TextField(
        blank=True,
        verbose_name=_("notes"),
        help_text=_("Damage description, observed conditions, additional actions taken."),
    )

    registered_by = models.ForeignKey(
        "producer.Staff",
        null=True, blank=True,
        on_delete=models.SET_NULL,
        verbose_name=_("registered by"),
    )
    registered_at = models.DateTimeField(auto_now_add=True, verbose_name=_("registered at"))
    updated_at    = models.DateTimeField(auto_now=True,     verbose_name=_("updated at"))

    class Meta:
        verbose_name        = _("alert outcome")
        verbose_name_plural = _("alert outcomes")

    def __str__(self):
        return f"Outcome — {self.alert.name} — {self.get_damage_severity_display()}"

    @property
    def has_damage(self):
        return self.damage_occurred and self.damage_severity != self.SEVERITY_NONE
