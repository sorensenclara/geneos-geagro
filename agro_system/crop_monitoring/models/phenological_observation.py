from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class PhenologicalObservation(models.Model):
    """
    Registro de campo: lo que el técnico observó realmente en el cultivo.

    El sistema mantiene siempre un estado calculado (GDD → calibración → BBCH).
    Esta tabla guarda cuándo el técnico ve algo distinto (o confirma lo calculado).

    Al guardar:
      - observed_gdd se completa automáticamente del acumulador (no lo tipea el usuario)
      - calculated_state guarda lo que el sistema decía en ese momento
      - Se recalibra PhenologicalCalibration para especie+zona+estadio observado
    """

    crop = models.ForeignKey(
        "operation.Crop",
        on_delete=models.CASCADE,
        related_name="phenological_observations",
        verbose_name=_("crop"),
    )
    date = models.DateField(
        default=timezone.localdate,
        verbose_name=_("observation date"),
    )
    observed_state = models.ForeignKey(
        "crop_monitoring.PhenologicalState",
        on_delete=models.PROTECT,
        related_name="observations",
        verbose_name=_("observed state"),
        help_text=_("BBCH stage actually seen in the field."),
    )
    # Se completa automáticamente del GDDAccumulator al guardar
    observed_gdd = models.DecimalField(
        max_digits=7, decimal_places=1,
        null=True, blank=True,
        verbose_name=_("GDD at observation"),
        help_text=_("GDD accumulated at the moment of observation. Auto-filled from accumulator."),
    )
    # Lo que el sistema calculaba en ese mismo momento (para comparar)
    calculated_state = models.ForeignKey(
        "crop_monitoring.PhenologicalState",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="calculated_observations",
        verbose_name=_("calculated state at observation"),
    )
    registered_by = models.ForeignKey(
        "producer.Staff",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name=_("registered by"),
    )
    notes = models.TextField(blank=True, verbose_name=_("notes"))

    class Meta:
        ordering = ["-date"]
        verbose_name = _("phenological observation")
        verbose_name_plural = _("phenological observations")

    def __str__(self):
        return f"{self.crop} — {self.observed_state} — {self.date}"

    @property
    def matches_calculated(self):
        """True si la observación coincide con lo que el sistema calculaba."""
        return self.observed_state_id == self.calculated_state_id

    def save(self, *args, **kwargs):
        self._auto_fill_gdd()
        self._auto_fill_calculated_state()
        super().save(*args, **kwargs)
        self._trigger_recalibration()

    # ------------------------------------------------------------------

    def _auto_fill_gdd(self):
        """Toma el GDD acumulado del acumulador 'vine' del cultivo."""
        if self.observed_gdd is not None:
            return
        try:
            biofix = self.crop.biofixes.get(counter="vine")
            self.observed_gdd = biofix.accumulator.accumulated_gdd
        except Exception:
            pass

    def _auto_fill_calculated_state(self):
        """Guarda el estado que el sistema calculaba en este momento."""
        if self.calculated_state_id is not None:
            return
        if self.observed_gdd is None:
            return
        from .phenological_state import PhenologicalState
        self.calculated_state = PhenologicalState.current_stage(
            vine_gdd=float(self.observed_gdd),
            specie=self.crop.activity.specie,
            area=self.crop.area,
        )

    def _trigger_recalibration(self):
        """Recalibra la calibración especie+zona+estadio con todas las observaciones."""
        from .phenological_calibration import PhenologicalCalibration
        try:
            cal = PhenologicalCalibration.objects.get(
                specie=self.crop.activity.specie,
                area=self.crop.area,
                state=self.observed_state,
            )
            cal.recalibrate_from_observations()
        except PhenologicalCalibration.DoesNotExist:
            pass   # sin calibración base para esta combo, nada que ajustar
