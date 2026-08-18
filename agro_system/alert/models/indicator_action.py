from django.db import models
from django.utils.translation import gettext_lazy as _


class IndicatorAction(models.Model):
    """
    Template de orden de trabajo para un indicador.

    Una acción define qué service crear cuando el indicador dispara.
    Todos los filtros son opcionales:
      - alert_level vacío → aplica a todos los niveles.
      - bbch_from/bbch_to nulos y stage nulo → aplica a cualquier estadio.
      - bbch_from/bbch_to nulos con stage → usa el rango BBCH del stage.
      - bbch_from/bbch_to con valores → override explícito del rango.

    stage también define la etapa de la WorkOrder resultante. Si es nulo, la OT
    se crea sin etapa asignada.

    create_on_forecast controla si la OT se emite en estado "Contingente"
    cuando la alerta viene del pronóstico (antes del evento).
    """

    LEVEL_CHOICES = [
        ("",         _("All levels")),
        ("warning",  _("Warning")),
        ("alert",    _("Alert")),
        ("critical", _("Critical")),
    ]

    indicator = models.ForeignKey(
        "alert.Indicator",
        on_delete=models.CASCADE,
        related_name="actions",
        verbose_name=_("indicator"),
    )
    alert_level = models.CharField(
        max_length=10,
        blank=True,
        choices=LEVEL_CHOICES,
        verbose_name=_("alert level"),
        help_text=_("Leave blank to match all levels."),
    )
    bbch_from = models.PositiveSmallIntegerField(
        null=True, blank=True,
        verbose_name=_("BBCH from"),
        help_text=_("Minimum BBCH code (inclusive). Leave blank for no lower bound."),
    )
    bbch_to = models.PositiveSmallIntegerField(
        null=True, blank=True,
        verbose_name=_("BBCH to"),
        help_text=_("Maximum BBCH code (inclusive). Leave blank for no upper bound."),
    )
    service = models.ForeignKey(
        "operation.Service",
        on_delete=models.CASCADE,
        verbose_name=_("service"),
    )
    stage = models.ForeignKey(
        "operation.Stage",
        null=True, blank=True,
        on_delete=models.SET_NULL,
        verbose_name=_("stage"),
        help_text=_(
            "Etapa operativa de la OT. Define también el rango BBCH si no se especifica "
            "bbch_from/bbch_to. Dejar vacío para que la acción aplique a cualquier estadio."
        ),
    )
    days_to_complete = models.PositiveSmallIntegerField(
        default=3,
        verbose_name=_("days to complete"),
        help_text=_("Work order deadline in days from emission date."),
    )
    create_on_forecast = models.BooleanField(
        default=False,
        verbose_name=_("create on forecast"),
        help_text=_(
            "Create the work order (in Contingente state) when the alert comes from "
            "forecast data. Enable for events that require advance preparation (frost, hail)."
        ),
    )

    def matches(self, level: str, bbch_code: int | None) -> bool:
        """
        True si esta acción aplica al nivel y BBCH dados.

        Rango BBCH efectivo (en orden de prioridad):
          1. bbch_from / bbch_to propios (override explícito)
          2. rango derivado del stage (bbch_from_int / bbch_to_int)
          3. None en ambos → sin restricción de BBCH (aplica siempre)
        """
        level_ok = not self.alert_level or self.alert_level == level

        if self.bbch_from is not None:
            eff_from = self.bbch_from
        elif self.stage_id is not None:
            eff_from = self.stage.bbch_from_int
        else:
            eff_from = None

        if self.bbch_to is not None:
            eff_to = self.bbch_to
        elif self.stage_id is not None:
            eff_to = self.stage.bbch_to_int
        else:
            eff_to = None

        from_ok = eff_from is None or (bbch_code is not None and eff_from <= bbch_code)
        to_ok   = eff_to   is None or (bbch_code is not None and eff_to   >= bbch_code)

        return level_ok and from_ok and to_ok

    def __str__(self):
        level_str = self.alert_level or "all levels"
        bbch_str  = f" BBCH {self.bbch_from}–{self.bbch_to}" if (self.bbch_from or self.bbch_to) else (
            f" [{self.stage}]" if self.stage_id else ""
        )
        return f"{self.indicator} [{level_str}{bbch_str}] → {self.service}"

    class Meta:
        verbose_name        = _("indicator action")
        verbose_name_plural = _("indicator actions")
        ordering = ["indicator", "alert_level", "bbch_from"]
