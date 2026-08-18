from django.db import models
from django.db.models import Min, Max, Avg, Count, Sum, Q
from django.utils.translation import gettext_lazy as _

from .weather_data import WeatherData
from .open_meteo_hourly import OpenMeteoHourly


class DailySummary(models.Model):
    """
    Resumen diario por lote: una fila por (lot, date).
    Es la capa de agregación que alimenta GDDAccumulator y las reglas de alerta.

    Dos métodos de consolidación, con prioridad estación > Open-Meteo:

      consolidate_from_station(lot, date)
          Lee WeatherData de lot.station, calcula tmin/tmax y contadores de horas.
          Sobreescribe cualquier fila previa (fuente_predominante='station').

      consolidate_from_open_meteo(lot, date)
          Lee OpenMeteoHourly del ExternalStation del lote.
          Solo crea/actualiza si NO existe ya una fila con fuente_predominante='station'
          para ese día (la estación real siempre gana).

    El management command diario llama primero a consolidate_from_open_meteo (disponible
    durante el día) y luego a consolidate_from_station al final del día.
    """

    SOURCE_STATION    = "station"
    SOURCE_OPEN_METEO = "open_meteo"
    SOURCE_CHOICES = [
        (SOURCE_STATION,    "Estación propia"),
        (SOURCE_OPEN_METEO, "Open-Meteo"),
    ]

    lot  = models.ForeignKey(
        "producer.Lot",
        on_delete=models.CASCADE,
        related_name="daily_summaries",
        verbose_name=_("lot"),
    )
    date = models.DateField(verbose_name=_("date"))

    # --- Temperatura ---
    tmin = models.DecimalField(max_digits=4, decimal_places=1, verbose_name=_("min temperature (°C)"))
    tmax = models.DecimalField(max_digits=4, decimal_places=1, verbose_name=_("max temperature (°C)"))

    # --- Humedad y agua ---
    hr_media  = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True, verbose_name=_("avg humidity (%)"))
    lluvia_mm = models.DecimalField(max_digits=5, decimal_places=1, default=0, verbose_name=_("rainfall (mm)"))
    eto_mm    = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True, verbose_name=_("ETo (mm)"))

    # --- Viento ---
    wind_max       = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True, verbose_name=_("max wind speed (km/h)"))
    wind_gusts_max = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True, verbose_name=_("max wind gusts (km/h)"))

    # --- Contadores de horas para alertas de enfermedades ---
    # Botrytis / Mildiu: horas con HR ≥ 90%
    horas_hr_alta     = models.PositiveSmallIntegerField(default=0, verbose_name=_("hours HR ≥ 90%"))
    # Gubler-Thomas (oídio): horas con T entre 21 y 30 °C
    horas_banda_oidio = models.PositiveSmallIntegerField(default=0, verbose_name=_("hours T 21–30 °C (oidio)"))

    fuente_predominante = models.CharField(
        max_length=12,
        choices=SOURCE_CHOICES,
        default=SOURCE_OPEN_METEO,
        verbose_name=_("source"),
    )

    class Meta:
        unique_together = ("lot", "date")
        ordering = ["date"]
        verbose_name = _("daily summary")
        verbose_name_plural = _("daily summaries")

    def __str__(self):
        return f"{self.lot} {self.date} — {self.tmin}/{self.tmax} °C [{self.fuente_predominante}]"

    # ------------------------------------------------------------------
    # Consolidación desde estación propia
    # ------------------------------------------------------------------
    @classmethod
    def consolidate_from_station(cls, lot, date):
        """
        Agrega WeatherData de lot.station para (lot, date).
        Sobreescribe la fila aunque ya exista un registro de Open-Meteo.
        Retorna el objeto, o None si la estación no tiene datos de temperatura ese día.

        horas_hr_alta / horas_banda_oidio cuentan filas (lecturas) con esa condición;
        si las lecturas son horarias el conteo equivale a horas reales.
        lluvia_mm = Max(rain_total) — acumulado diario que resetea la estación a medianoche.
        eto_mm queda null (viene de Open-Meteo, se puede completar externamente).
        """
        if not lot.station_id:
            return None

        agg = (
            WeatherData.objects
            .filter(station=lot.station, timestamp__date=date, temp__isnull=False)
            .aggregate(
                tmin=Min("temp"),
                tmax=Max("temp"),
                hr_media=Avg("humidity"),
                lluvia_mm=Max("rain_total"),
                wind_max=Max("wind_speed"),
                wind_gusts_max=Max("wind_gust_max"),
                horas_hr_alta=Count("id", filter=Q(humidity__gte=90)),
                horas_banda_oidio=Count("id", filter=Q(temp__gte=21, temp__lte=30)),
            )
        )
        if agg["tmin"] is None:
            return None

        obj, _ = cls.objects.update_or_create(
            lot=lot,
            date=date,
            defaults={
                "tmin":               round(agg["tmin"], 1),
                "tmax":               round(agg["tmax"], 1),
                "hr_media":           round(agg["hr_media"], 1) if agg["hr_media"] is not None else None,
                "lluvia_mm":          round(agg["lluvia_mm"] or 0, 1),
                "wind_max":           round(agg["wind_max"], 1) if agg["wind_max"] is not None else None,
                "wind_gusts_max":     round(agg["wind_gusts_max"], 1) if agg["wind_gusts_max"] is not None else None,
                "horas_hr_alta":      agg["horas_hr_alta"],
                "horas_banda_oidio":  agg["horas_banda_oidio"],
                "fuente_predominante": cls.SOURCE_STATION,
            },
        )
        return obj

    # ------------------------------------------------------------------
    # Consolidación desde Open-Meteo (horario + diario)
    # ------------------------------------------------------------------
    @classmethod
    def consolidate_from_open_meteo(cls, lot, date, external_station=None):
        """
        Crea/actualiza el resumen desde OpenMeteoHourly.
        Si ya existe una fila con fuente_predominante='station' no hace nada.

        Todos los valores se calculan desde OpenMeteoHourly.data (JSONField).
        Los nombres de clave se resuelven contra los mapeos de la estación para
        encontrar temperatura, humedad, precipitación y ETo configurados.
        """
        existing = cls.objects.filter(lot=lot, date=date).first()
        if existing and existing.fuente_predominante == cls.SOURCE_STATION:
            return existing

        hourly_qs = OpenMeteoHourly.objects.filter(datetime__date=date)
        if external_station:
            hourly_qs = hourly_qs.filter(station=external_station)

        if not hourly_qs.exists():
            return None

        agg = hourly_qs.filter(temperature__isnull=False).aggregate(
            tmin=Min("temperature"),
            tmax=Max("temperature"),
            hr_media=Avg("humidity"),
            lluvia_mm=Sum("precipitation"),
            eto_mm=Sum("eto_mm"),
            wind_max=Max("wind_speed"),
            wind_gusts_max=Max("wind_gusts"),
            horas_hr_alta=Count("id", filter=Q(humidity__gte=90)),
            horas_banda_oidio=Count("id", filter=Q(temperature__gte=21, temperature__lte=30)),
        )
        if agg["tmin"] is None:
            return None

        obj, _ = cls.objects.update_or_create(
            lot=lot,
            date=date,
            defaults={
                "tmin":               round(float(agg["tmin"]), 1),
                "tmax":               round(float(agg["tmax"]), 1),
                "hr_media":           round(float(agg["hr_media"]), 1) if agg["hr_media"] else None,
                "lluvia_mm":          round(float(agg["lluvia_mm"]), 1) if agg["lluvia_mm"] else 0,
                "eto_mm":             round(float(agg["eto_mm"]), 1) if agg["eto_mm"] else None,
                "wind_max":           round(float(agg["wind_max"]), 1) if agg["wind_max"] else None,
                "wind_gusts_max":     round(float(agg["wind_gusts_max"]), 1) if agg["wind_gusts_max"] else None,
                "horas_hr_alta":      agg["horas_hr_alta"],
                "horas_banda_oidio":  agg["horas_banda_oidio"],
                "fuente_predominante": cls.SOURCE_OPEN_METEO,
            },
        )
        return obj
