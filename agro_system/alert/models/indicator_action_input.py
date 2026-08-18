from django.db import models
from django.utils.translation import gettext_lazy as _


class IndicatorActionInput(models.Model):
    """
    Insumo requerido por una IndicatorAction.

    Al crear la orden de trabajo se copia como InputWorkOrder con dose_applied=None
    (la dosis planificada; la aplicada la registra el operario).
    """

    action = models.ForeignKey(
        "alert.IndicatorAction",
        on_delete=models.CASCADE,
        related_name="inputs",
        verbose_name=_("action"),
    )
    input = models.ForeignKey(
        "input.Input",
        on_delete=models.CASCADE,
        verbose_name=_("input"),
    )
    dose = models.FloatField(
        verbose_name=_("planned dose"),
        help_text=_("Dose per application in the input's unit of measure."),
    )

    def __str__(self):
        return f"{self.input} — {self.dose} ({self.action})"

    class Meta:
        verbose_name        = _("indicator action input")
        verbose_name_plural = _("indicator action inputs")
