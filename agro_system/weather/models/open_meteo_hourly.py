from django.db import models
from django.utils.translation import gettext_lazy as _


class OpenMeteoHourly(models.Model):
    """
    Datos horarios de Open-Meteo por estación externa.
    Se sobreescribe con update_or_create sobre (station, datetime).

    Las 8 variables estándar tienen columna propia para facilitar agregaciones en DB.
    Cualquier variable adicional configurada en ExternalStationVariable va a extra_data
    con la misma clave (source_field) que se definió en el admin.
    """

    station  = models.ForeignKey(
        "weather.ExternalStation",
        on_delete=models.CASCADE,
        related_name="hourly_readings",
        verbose_name=_("station"),
    )
    datetime = models.DateTimeField(verbose_name=_("datetime"))

    # Variables estándar de Open-Meteo
    temperature    = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, verbose_name=_("temperature (°C)"))
    humidity       = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, verbose_name=_("relative humidity (%)"))
    wind_speed     = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, verbose_name=_("wind speed (km/h)"))
    wind_direction = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True, verbose_name=_("wind direction (°)"))
    wind_gusts     = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, verbose_name=_("wind gusts (km/h)"))
    precipitation  = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, verbose_name=_("precipitation (mm)"))
    cape           = models.DecimalField(max_digits=7, decimal_places=1, null=True, blank=True, verbose_name=_("CAPE (J/kg)"))
    eto_mm         = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, verbose_name=_("ETo FAO-56 (mm)"))

    # Variables derivadas: calculadas al guardar, comparando con la hora anterior
    delta_t_1h        = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True,
        verbose_name=_("delta T (°C/h)"),
        help_text=_("Temperature change vs previous hour. Negative = drop."),
    )
    wind_dir_change_1h = models.DecimalField(
        max_digits=5, decimal_places=1, null=True, blank=True,
        verbose_name=_("wind direction change (°/h)"),
        help_text=_("Angular wind direction change vs previous hour (0–180°)."),
    )

    # Variables adicionales configuradas en el admin (clave = source_field de la API)
    extra_data = models.JSONField(default=dict, blank=True, verbose_name=_("extra data"))

    class Meta:
        unique_together = ("station", "datetime")
        ordering        = ["datetime"]
        verbose_name         = _("Open-Meteo hourly data")
        verbose_name_plural  = _("Open-Meteo hourly data")

    def __str__(self):
        return f"{self.station} {self.datetime:%Y-%m-%d %H:%M}"
