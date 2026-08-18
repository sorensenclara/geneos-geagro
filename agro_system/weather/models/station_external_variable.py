from django.db import models
from django.utils.translation import gettext_lazy as _


class ExternalStationVariable(models.Model):
    """
    Mapeo entre una variable climática estándar del sistema y el nombre
    que usa esa variable en la API de la estación externa.

    Ejemplo para Open-Meteo:
      variable    → VarCropTechnique("Precipitación")
      source_field → "precipitation"
    """

    station = models.ForeignKey(
        "weather.ExternalStation",
        on_delete=models.CASCADE,
        related_name="variable_mappings",
        verbose_name=_("station"),
    )
    variable = models.ForeignKey(
        "parameter.VarCropTechnique",
        on_delete=models.CASCADE,
        related_name="station_mappings",
        limit_choices_to={"is_climatic": True},
        verbose_name=_("variable"),
    )
    source_field = models.CharField(
        max_length=100,
        verbose_name=_("source field"),
        help_text=_("Nombre exacto del campo en la respuesta de la API (ej: temperature_2m)."),
    )

    class Meta:
        unique_together = ("station", "variable")
        verbose_name = _("station variable mapping")
        verbose_name_plural = _("station variable mappings")

    def __str__(self):
        return f"{self.station} — {self.variable} → {self.source_field}"
