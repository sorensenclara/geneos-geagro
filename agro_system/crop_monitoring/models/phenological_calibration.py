from django.db import models
from django.db.models import Avg
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class PhenologicalCalibration(models.Model):
    """
    GDD desde–hasta para un estadio fenológico, específico por especie y zona.

    Arranca con valores base (seed). Se va ajustando automáticamente cada vez
    que un técnico registra una observación de campo para esa especie+zona+estadio.
    El ajuste usa el promedio de todas las observaciones acumuladas.

    Usar seed_phenological_calibrations(specie, area) para poblar la tabla inicial.
    """

    specie = models.ForeignKey(
        "parameter.Specie",
        on_delete=models.CASCADE,
        related_name="phenological_calibrations",
        verbose_name=_("specie"),
    )
    area = models.ForeignKey(
        "parameter.Area",
        on_delete=models.CASCADE,
        related_name="phenological_calibrations",
        verbose_name=_("area"),
    )
    state = models.ForeignKey(
        "crop_monitoring.PhenologicalState",
        on_delete=models.CASCADE,
        related_name="calibrations",
        verbose_name=_("phenological state"),
    )
    gdd_from = models.PositiveIntegerField(verbose_name=_("GDD from"))
    gdd_to   = models.PositiveIntegerField(verbose_name=_("GDD to"))

    # Metadatos de calibración automática
    is_auto_calibrated = models.BooleanField(
        default=False,
        verbose_name=_("auto calibrated"),
        help_text=_("True when adjusted from field observations."),
    )
    sample_count = models.PositiveIntegerField(
        default=0,
        verbose_name=_("sample count"),
        help_text=_("Number of field observations used in the last calibration."),
    )
    last_calibrated = models.DateField(
        null=True, blank=True,
        verbose_name=_("last calibrated"),
    )

    class Meta:
        unique_together = ("specie", "area", "state")
        ordering = ["state__order"]
        verbose_name = _("phenological calibration")
        verbose_name_plural = _("phenological calibrations")

    def __str__(self):
        status = f"auto:{self.sample_count}" if self.is_auto_calibrated else "base"
        return f"{self.specie} · {self.area} · {self.state} [{self.gdd_from}–{self.gdd_to} GDD] ({status})"

    def recalibrate_from_observations(self):
        """
        Recalcula gdd_from como promedio de todas las observaciones de campo
        para esta combinación especie+zona+estadio.
        El ancho de la ventana (gdd_to - gdd_from) se preserva.

        Además encadena los estadios adyacentes para evitar solapamientos o huecos:
          - Estadio anterior: su gdd_to se ajusta a new_gdd_from - 1
          - Estadio siguiente: su gdd_from se ajusta a new_gdd_to + 1

        Se llama automáticamente al guardar una PhenologicalObservation.
        """
        from .phenological_observation import PhenologicalObservation

        obs = PhenologicalObservation.objects.filter(
            crop__activity__specie=self.specie,
            crop__area=self.area,
            observed_state=self.state,
            observed_gdd__isnull=False,
        )
        count = obs.count()
        if count == 0:
            return

        avg_gdd        = obs.aggregate(avg=Avg("observed_gdd"))["avg"]
        width          = self.gdd_to - self.gdd_from
        new_gdd_from   = round(avg_gdd)
        new_gdd_to     = new_gdd_from + width

        self.gdd_from           = new_gdd_from
        self.gdd_to             = new_gdd_to
        self.sample_count       = count
        self.last_calibrated    = timezone.localdate()
        self.is_auto_calibrated = True
        self.save()

        # Encadenar estadio anterior: su gdd_to no puede solaparse con este gdd_from
        prev_cal = (
            PhenologicalCalibration.objects
            .filter(specie=self.specie, area=self.area,
                    state__order__lt=self.state.order)
            .order_by("-state__order")
            .first()
        )
        if prev_cal and prev_cal.gdd_to >= new_gdd_from:
            prev_cal.gdd_to = new_gdd_from - 1
            prev_cal.save(update_fields=["gdd_to"])

        # Encadenar estadio siguiente: su gdd_from no puede solaparse con este gdd_to
        next_cal = (
            PhenologicalCalibration.objects
            .filter(specie=self.specie, area=self.area,
                    state__order__gt=self.state.order)
            .order_by("state__order")
            .first()
        )
        if next_cal and next_cal.gdd_from <= new_gdd_to:
            next_cal.gdd_from = new_gdd_to + 1
            next_cal.save(update_fields=["gdd_from"])


def seed_phenological_calibrations(specie, area):
    """
    Carga calibraciones base para la combinación especie+zona,
    copiando los gdd_from/gdd_to actuales de PhenologicalState.
    Llamar desde management command o data migration.
    Solo crea registros que no existen; no pisa calibraciones ya ajustadas.
    """
    from .phenological_state import PhenologicalState

    created = 0
    for state in PhenologicalState.objects.all():
        _, was_created = PhenologicalCalibration.objects.get_or_create(
            specie=specie,
            area=area,
            state=state,
            defaults={
                "gdd_from": state.gdd_from,
                "gdd_to":   state.gdd_to,
            },
        )
        if was_created:
            created += 1
    return created
