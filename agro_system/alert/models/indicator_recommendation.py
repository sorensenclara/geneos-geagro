from django.db import models
from django.utils.translation import gettext_lazy as _


class IndicatorRecommendation(models.Model):
    """
    Recomendación informativa asociada a un indicador.

    A diferencia de IndicatorAction, no genera una orden de trabajo:
    se muestra en pantalla como texto informativo cuando la alerta dispara.

    Todos los filtros son opcionales:
      - alert_level vacío → aplica a todos los niveles.
      - bbch_from / bbch_to nulos → aplica a cualquier estadio BBCH.
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
        related_name="recommendations",
        verbose_name=_("indicator"),
    )
    alert_level = models.CharField(
        max_length=10,
        blank=True,
        choices=LEVEL_CHOICES,
        verbose_name=_("alert level"),
        help_text=_("Dejar vacío para aplicar a todos los niveles."),
    )
    bbch_from = models.PositiveSmallIntegerField(
        null=True, blank=True,
        verbose_name=_("BBCH from"),
        help_text=_("Código BBCH mínimo (inclusivo). Vacío = sin límite inferior."),
    )
    bbch_to = models.PositiveSmallIntegerField(
        null=True, blank=True,
        verbose_name=_("BBCH to"),
        help_text=_("Código BBCH máximo (inclusivo). Vacío = sin límite superior."),
    )
    text = models.TextField(
        verbose_name=_("recommendation"),
        help_text=_("Texto que se mostrará al usuario cuando la alerta se active."),
    )
    order = models.PositiveSmallIntegerField(
        default=0,
        verbose_name=_("order"),
    )

    def matches(self, level: str, bbch_code: int | None) -> bool:
        """True si esta recomendación aplica al nivel y BBCH actuales."""
        level_ok = not self.alert_level or self.alert_level == level
        from_ok  = self.bbch_from is None or (bbch_code is not None and self.bbch_from <= bbch_code)
        to_ok    = self.bbch_to   is None or (bbch_code is not None and self.bbch_to   >= bbch_code)
        return level_ok and from_ok and to_ok

    def __str__(self):
        level_label = self.get_alert_level_display() or "Todos los niveles"
        bbch_label  = ""
        if self.bbch_from is not None:
            bbch_label = f" | BBCH {self.bbch_from}–{self.bbch_to or '∞'}"
        return f"{self.indicator} — {level_label}{bbch_label}"

    class Meta:
        ordering            = ("order", "id")
        verbose_name        = _("recommendation")
        verbose_name_plural = _("recommendations")
